import json
from multiprocessing import Pool

from flask import Blueprint, current_app, jsonify, make_response, request

from .tasks import infer_task

from .libs.db import get_db
from .libs.models import Model, Order, User
from .libs.utils import (check_job_status, error_response, ok_response,
                         query_model_params, submit_data, submit_infer_task,
                         submit_train_task)

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
    attributes = data.get('attributes')
    label_name = data.get('label_name')
    original_attr = attributes
    unique_id = data.get('unique_id')
    attributes = [unique_id] + attributes + [label_name]
    label_value = data.get('label_value')

    db = get_db()
    initiator = db.query(User).filter(User.id == user_id).first()
    hosts = [db.query(User).filter(User.id == uid).first() for uid in party_id]

    id_map = {user.party_id: user.id for user in [initiator] + hosts}

    responses = {}
    p = Pool(len(data_info))
    for k, v in data_info.items():
        user = db.query(User).filter(User.id==k).first()
        url = user.client_url + "/api/read_data"
        responses[user.party_id] = p.apply_async(submit_data, args=(url, v, attributes, label_value, ))
    p.close()
    p.join()
    data_volum = dict()
    for pid in id_map.keys():
        response = json.loads(responses[pid].get().text)
        if response['code'] != 200:
            return error_response(message=response)
        data_volum[id_map[pid]] = response['info']['data_volum']

    # Generate config file
    with open(current_app.config['TRAIN_TEMPLATE'], 'r', encoding='utf-8') as f:
        conf_dict = json.loads(f.read())

        conf_dict['initiator']['party_id'] = initiator.party_id
        conf_dict['initiator']['role'] = 'guest'

        conf_dict['role']['guest'] = [initiator.party_id]
        conf_dict['role']['host'] = [host.party_id for host in hosts]
        conf_dict['role']['arbiter'] = [initiator.party_id]

        # DO NOT CHANGE
        conf_dict['role_parameters']['guest']['args']['data']['train_data'] = [{'namespace': json.loads(responses[pid].get().text)['data']['data']['namespace'], 'name': json.loads(responses[pid].get().text)['data']['data']['table_name']} for pid in conf_dict['role']['guest']]
        conf_dict['role_parameters']['host']['args']['data']['train_data'] = [{'namespace': json.loads(responses[pid].get().text)['data']['data']['namespace'], 'name': json.loads(responses[pid].get().text)['data']['data']['table_name']} for pid in conf_dict['role']['host']]

        conf_dict['algorithm_parameters']['homo_lr_0'] = model_param

        conf_dict['algorithm_parameters']['dataio_0']['label_name'] = label_name

    # Read DSL file
    with open(current_app.config['LR_DSL_TEMPLATE'], 'r', encoding='utf-8') as f:
        dsl_dict = json.loads(f.read())

    # print(conf_dict, dsl_dict)

    response = submit_train_task(initiator.client_url+'/api/training_task', conf_dict, dsl_dict)

    model_info = json.loads(response.text)['data']['data']['model_info']
    model_id = model_info['model_id']
    model_version = model_info['model_version']

    print(model_info)
    model_param['attributes'] = original_attr
    model_param['unique_id'] = unique_id
    model_param['label_name'] = label_name
    model_param['data_volum'] = data_volum
    model = Model(model_id, model_version, json.dumps(model_param))
    order = Order(model_version, "train", json.dumps(data), json.dumps(conf_dict))
    initiator.models.append(model)
    order.model = model
    db.add(model)
    db.add(order)
    db.commit()

    return ok_response(data={"model_id": model.id, "order_id": order.id, "data_volum": data_volum})


@bp.route('/train_status', methods=['GET'])
def train_status():
    order_id = request.args.get('order_id')

    if order_id is None:
        return error_response("None data.")

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
    return ok_response(message=status_info['message'], data={'model_id': model_id, 'train_status':status_info['data']})


@bp.route('/infer', methods=['POST'])
def model_infer():
    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()
    model_id = data.get('model_id')
    user_id = data.get('input_data').get('user_id')
    data_sql = data.get('input_data').get('data_sql')

    db = get_db()

    model = db.query(Model).filter(Model.id == model_id).first()

    fate_job_id = model.fate_version
    model_owner = model.users[0]
    party_id = str(model_owner.party_id)
    role = "guest"
    cpn = "homo_lr_0"
    url = model_owner.client_url + '/api/get_model_params'

    response = query_model_params(url, fate_job_id, party_id, role, cpn)
    model_weights = json.loads(response.text)
    model_info = json.loads(model.info)
    unique_id = model_info['unique_id']
    attributes = model_info['attributes']
    
    predict_user = db.query(User).filter(User.id==user_id).first()
    url = predict_user.client_url + '/api/infer'
    job_info = {'infer_status': 'runnning', 'result': ''}
    order = Order(type="infer", order_info=data, job_info=json.dumps(job_info))
    db.add(order)
    db.commit()
    infer_task.delay(url, data_sql, model_weights, attributes, unique_id, order.id)
    return ok_response(data={'order_id': order.id})


@bp.route('/infer_status/', methods=['GET'])
def infer_status():
    order_id = request.args.get('order_id')
    if order_id is None:
        return error_response("None order_id.")

    db = get_db()
    order = db.query(Order).filter(Order.id==order_id).first()
    if order is None:
        return error_response("No order found! Please check your order_id.")

    if order.type != "infer":
        return error_response("The order is not a inference order, please check your order_id.")

    return ok_response(data=json.loads(order.job_info))


@bp.route('/info/', methods=['GET'])
def model_info():
    model_id = request.args.get('model_id')

    if model_id is None:
        return error_response("None model_id.")

    db = get_db()
    model = db.query(Model).filter(Model.id == model_id).first()

    if (model is None):
        return error_response("Error model_id.")

    response = {}
    model_owner = model.users[0]
    model_info = json.loads(model.info)
    data_volum = model_info['data_volum']
    model_info.pop('data_volum')
    response['model_params'] = model_info
    response['user_id'] = model_owner.id
    response['model_type'] = 'Logistic Regression'

    order_info = {}
    for order in model.orders:
        if order.type == 'train':
            order_info = json.loads(order.order_info)
            break
    response['party_id'] = order_info.get('party_id')
    response['data_volum'] = data_volum
    return ok_response(data=response)
