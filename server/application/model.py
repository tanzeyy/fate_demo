from multiprocessing import Pool

from flask import Blueprint, jsonify, make_response, request, current_app
from .libs.utils import ok_response, error_response, submit_data, submit_train_task, check_job_status
from .libs.db import get_db
from .libs.models import User, Model, Order
import json

bp = Blueprint('model', __name__, url_prefix='/model')

@bp.route('/train', methods=['POST', ])
def model_train():
    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()
    user_id = data.get('user_id')
    model_type = data.get('model_type')
    model_param = data.get('model_params')
    party_id = data.get('party_id')
    data_info = data.get('data_info')

    db = get_db()
    initiator = db.query(User).filter(User.id == user_id).first()
    hosts = [db.query(User).filter(User.id == uid).first() for uid in party_id]

    responses = {}
    p = Pool(len(data_info))
    for k, v in data_info.items():
        user = db.query(User).filter(User.id==k).first()
        url = user.client_url + "/api/read_data"
        responses[user.party_id] = p.apply_async(submit_data, args=(url, v, ))
    p.close()
    p.join()

    # Generate config file
    with open(current_app.config['TRAIN_TEMPLATE'], 'r', encoding='utf-8') as f:
        conf_dict = json.loads(f.read())

        conf_dict['initiator']['party_id'] = initiator.party_id
        conf_dict['initiator']['role'] = 'guest'

        conf_dict['role']['guest'] = [initiator.party_id]
        conf_dict['role']['host'] = [host.party_id for host in hosts]
        conf_dict['role']['arbiter'] = [initiator.party_id]

        # DO NOT CHANGE
        conf_dict['role_parameters']['guest']['args']['data']['train_data'] = [{'namespace': json.loads(responses[uid].get().text)['data']['data']['namespace'], 'name': json.loads(responses[uid].get().text)['data']['data']['table_name']} for uid in conf_dict['role']['guest']]
        conf_dict['role_parameters']['host']['args']['data']['train_data'] = [{'namespace': json.loads(responses[uid].get().text)['data']['data']['namespace'], 'name': json.loads(responses[uid].get().text)['data']['data']['table_name']} for uid in conf_dict['role']['host']]

        conf_dict['algorithm_parameters']['homo_lr_0'] = model_param

    # Read DSL file
    with open(current_app.config['LR_DSL_TEMPLATE'], 'r', encoding='utf-8') as f:
        dsl_dict = json.loads(f.read())

    # print(conf_dict, dsl_dict)

    response = submit_train_task(initiator.client_url+'/api/training_task', conf_dict, dsl_dict)

    model_info = json.loads(response.text)['data']['data']['model_info']
    model_id = model_info['model_id']
    model_version = model_info['model_version']

    print(model_info)

    model = Model(model_id, model_version, json.dumps(model_param))
    order = Order(model_version, "train", json.dumps(data), json.dumps(conf_dict))
    initiator.models.append(model)
    order.model = model
    db.add(model)
    db.add(order)
    db.commit()

    return ok_response(data={"model_id": model.id, "order_id": order.id})


@bp.route('/train_status', methods=['POST'])
def train_status():
    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()
    order_id = data.get('order_id')

    db = get_db()
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        return error_response(message="Error order_id")

    model_id = order.model_id
    fate_job_id = order.fate_job_id
    job_info = json.loads(order.order_info)
    user_id = job_info['user_id']
    user = db.query(User).filter(User.id == user_id).first()
    url = user.client_url + "/api/status"
    response = check_job_status(url, fate_job_id)

    status_info = json.loads(response.text)
    return ok_response(message=status_info['message'], data={'order_id':order_id, 'model_id': model_id, 'train_status':status_info['data']})


