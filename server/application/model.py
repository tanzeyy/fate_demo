import json

from flask import Blueprint, current_app, jsonify, make_response, request

from .libs.db import get_db
from .libs.models import Model, Order, User
from .libs.utils import (check_job_status, error_response, ok_response,
                         query_model_params, submit_data, submit_infer_task,
                         submit_train_task)
from .tasks import infer_task, train_task

bp = Blueprint('model', __name__, url_prefix='/model')


@bp.route('/train', methods=['POST', ])
def model_train():
    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()
    model = Model()
    order = Order(type='train', order_info=json.dumps(data))
    order.model = model

    db = get_db()
    db.add(model)
    db.add(order)
    db.commit()
    train_conf_template = current_app.config['TRAIN_TEMPLATE']
    dsl_template = current_app.config['LR_DSL_TEMPLATE']
    train_task.delay(data, train_conf_template,
                     dsl_template, order.id, model.id)

    return ok_response(data={"model_id": model.id, "order_id": order.id})


@bp.route('/train_status', methods=['GET'])
def train_status():
    order_id = request.args.get('order_id')

    if order_id is None:
        return error_response("None data.")

    db = get_db()
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        return error_response(message="Error order_id.")

    if order.type != 'train':
        return error_response(message="Not a training order.")

    if order.job_info is None:
        return error_response(message='Job submit failed.')

    if order.fate_job_id is None:
        return ok_response(data=json.loads(order.job_info))

    job_info = json.loads(order.job_info)
    data_volum = job_info['algorithm_parameters']['homo_lr_0']['data_volum']

    model_id = order.model_id
    fate_job_id = order.fate_job_id
    order_info = json.loads(order.order_info)
    user_id = order_info['user_id']
    user = db.query(User).filter(User.id == user_id).first()
    url = user.client_url + "/api/status"
    response = check_job_status(url, fate_job_id)

    status_info = json.loads(response.text)
    return ok_response(message=status_info['message'], data={'model_id': model_id, 'train_status': status_info['data'], "data_volum": data_volum})


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

    predict_user = db.query(User).filter(User.id == user_id).first()
    url = predict_user.client_url + '/api/infer'
    job_info = {'infer_status': 'runnning', 'result': ''}
    order = Order(type="infer", order_info=data, job_info=json.dumps(job_info))
    db.add(order)
    db.commit()
    infer_task.delay(url, data_sql, model_weights,
                     attributes, unique_id, order.id)
    return ok_response(data={'order_id': order.id})


@bp.route('/infer_status/', methods=['GET'])
def infer_status():
    order_id = request.args.get('order_id')
    if order_id is None:
        return error_response("None order_id.")

    db = get_db()
    order = db.query(Order).filter(Order.id == order_id).first()
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


@bp.route('/board_url', methods=['GET'])
def board_url():
    order_id = request.args.get('order_id')

    if order_id is None:
        return error_response("None order_id.")

    db = get_db()
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        return error_response(message="Error order_id")

    if order.type != 'train':
        return error_response(message="Not a training order id")
    
    if order.fate_job_id is None:
        return error_response(message="No job id found, please check order status.")

    # TODO：外网和端口
    # nginx_conf = {'1':'', '2':'', '3': '', '4': ''}

    url = "{}/#/dashboard?job_id={}&role={}&party_id={}"
    job_info = json.loads(order.order_info)
    fate_job_id = order.fate_job_id

    board_url = dict()

    def gen_url(user_id, role):
        user = db.query(User).filter(User.id == user_id).first()
        client_url = user.client_url.replace('5000', '8080')
        return url.format(client_url, fate_job_id, role, user.party_id)

    board_url[job_info['user_id']] = gen_url(job_info['user_id'], 'guest')
    for user in job_info['party_id']:
        board_url[user] = gen_url(user, 'host')

    return ok_response(data={'board_url': board_url})
