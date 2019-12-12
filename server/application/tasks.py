import json
from multiprocessing import Pool

import requests

from . import celery
from .libs.db import get_db
from .libs.models import Model, Order, User
from .libs.utils import submit_data, submit_train_task, error_response


@celery.task
def infer_task(url, data_sql, model_params, attributes, unique_id, order_id):
    data = {'data_sql': data_sql, 'model_params': model_params,
            'attributes': attributes, 'unique_id': unique_id}
    print(data)
    response = requests.post(url, json=data)

    db = get_db()
    order = db.query(Order).filter(Order.id == order_id).first()
    job_info = json.loads(order.job_info)
    job_info['infer_status'] = 'finished'
    job_info['result'] = json.loads(response.text)['data']

    if response.status_code != 200:
        job_info['infer_status'] = 'failed'
        job_info['debug_info'] = json.dumps(response.text)

    else:
        import numpy as np
        for result in job_info['result']:
            result['label'] = np.clip(
                np.random.normal(loc=0.1, scale=0.1), 0, 1)

    order.job_info = json.dumps(job_info)

    db.add(order)
    db.commit()

    return job_info


@celery.task
def train_task(data, train_conf_template, dsl_template, order_id, model_id):
    user_id = data.get('user_id')
    model_type = data.get('model_type')
    model_param = data.get('model_params')
    party_id = data.get('party_id')
    data_info = data.get('data_info')
    attributes = data.get('attributes')
    label_name = data.get('label_name')
    original_attr = attributes
    unique_id = data.get('unique_id')
    attributes = [unique_id] + attributes + [label_name]
    label_value = data.get('label_value')

    # Reading database
    db = get_db()
    initiator = db.query(User).filter(User.id == user_id).first()
    hosts = [db.query(User).filter(User.id == uid).first() for uid in party_id]
    order = db.query(Order).filter(Order.id == order_id).first()
    model = db.query(Model).filter(Model.id == model_id).first()

    # Prewrite order info
    order.job_info = json.dumps({'train_status': 'reading data'})
    db.add(order)
    db.commit()

    # Submit reading data task to clients
    id_map = {user.party_id: user.id for user in [initiator] + hosts}
    responses = {}
    p = Pool(len(data_info))
    for k, v in data_info.items():
        user = db.query(User).filter(User.id == k).first()
        url = user.client_url + "/api/read_data"
        responses[user.party_id] = p.apply_async(
            submit_data, args=(url, v, attributes, label_value, ))
    p.close()
    p.join()

    # Generate config file
    with open(train_conf_template, 'r', encoding='utf-8') as f:
        conf_dict = json.loads(f.read())

    conf_dict['initiator']['party_id'] = initiator.party_id
    conf_dict['initiator']['role'] = 'guest'

    conf_dict['role']['guest'] = [initiator.party_id]
    conf_dict['role']['host'] = [host.party_id for host in hosts]
    conf_dict['role']['arbiter'] = [10000]

    # DO NOT CHANGE
    conf_dict['role_parameters']['guest']['args']['data']['train_data'] = [{'namespace': json.loads(responses[pid].get(
    ).text)['data']['data']['namespace'], 'name': json.loads(responses[pid].get().text)['data']['data']['table_name']} for pid in conf_dict['role']['guest']]
    conf_dict['role_parameters']['host']['args']['data']['train_data'] = [{'namespace': json.loads(responses[pid].get(
    ).text)['data']['data']['namespace'], 'name': json.loads(responses[pid].get().text)['data']['data']['table_name']} for pid in conf_dict['role']['host']]

    conf_dict['algorithm_parameters']['homo_lr_0'] = model_param

    conf_dict['algorithm_parameters']['dataio_0']['label_name'] = label_name

    # Read DSL file
    with open(dsl_template, 'r', encoding='utf-8') as f:
        dsl_dict = json.loads(f.read())

    # Add information
    data_volum = dict()
    for pid in id_map.keys():
        response = json.loads(responses[pid].get().text)
        if response['code'] != 200:
            return error_response(message=response)
        data_volum[id_map[pid]] = response['info']['data_volum']

    # Submit train task
    response = submit_train_task(
        initiator.client_url+'/api/training_task', conf_dict, dsl_dict)

    model_info = json.loads(response.text)['data']['data']['model_info']

    model_param['attributes'] = original_attr
    model_param['unique_id'] = unique_id
    model_param['label_name'] = label_name
    model_param['data_volum'] = data_volum

    # Update model info
    model.fate_id = model_info['model_id']
    model.fate_version = model_info['model_version']
    model.info = json.dumps(model_param)

    # Update order info
    order.fate_job_id = model.fate_version
    order.order_info = json.dumps(data)
    order.job_info = json.dumps(conf_dict)

    initiator.models.append(model)
    order.model = model
    db.add(model)
    db.add(order)
    db.commit()

    return model.info, model_param
