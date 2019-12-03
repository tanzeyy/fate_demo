from flask import Blueprint, jsonify, make_response, request, current_app
from .utils import ok_response, error_response, upload_json, exec_upload_task, get_timeid, exec_modeling_task, job_status_checker, get_model, generate_csv, get_dataframe
from .db import get_db
import time
import csv
import json
import os

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/read_data', methods=['POST'])
def read_data():
    '''
    根据sql语句读取数据
    生成csv
    '''

    # 没有查询的sql语句
    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()

    sql = data.get('data_sql')
    # 没有sql语句
    if not sql:
        return error_response(message="None data_sql in request.")

    db = get_db()
    db_data = None
    try:
        db_data = db.execute(r'''{}'''.format(sql)).fetchall()
    except Exception as e:
        return error_response(message="Query data from database error. Error info: " + str(e))

    if (len(db_data) == 0):
        return error_response(message="没有满足条件的数据")

    table_head = len(db_data[0])
    if (table_head < 2):
        return error_response(message="数据缺少id或者标签")

    tmp_path = current_app.config['TEMP_DATA_DIR']

    prefix, file_path = generate_csv(db_data=db_data, tmp_path=tmp_path)

    template = current_app.config['UPLOAD_TEMPLATE']
    conf_json = upload_json(file_path, prefix, template)
    fate_flow_path = current_app.config['FATE_FLOW_PATH']

    stdout = exec_upload_task(conf_json, "", fate_flow_path)    

    return ok_response(data=stdout)


@bp.route('/training_task', methods=['POST'])
def training_task():
    '''
    根据config dict执行任务
    '''

    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()
    config_dict = data.get('config_dict')
    dsl_dict = data.get('dsl_dict')
    fate_flow_path = current_app.config['FATE_FLOW_PATH']

    stdout = exec_modeling_task(dsl_dict, config_dict, fate_flow_path)

    return ok_response(data=stdout)


@bp.route('/inference_task', methods=['POST'])
def inference_task():
    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()
    config_dict = data.get('config_dict')
    fate_flow_path = current_app.config['FATE_FLOW_PATH']


@bp.route('/status', methods=['POST'])
def check_status():
    if not request.data:
        return error_response(message="None data.")

    data = request.get_json()
    fate_job_id = data.get('fate_job_id')
    fate_flow_path = current_app.config['FATE_FLOW_PATH']
    stdout = job_status_checker(fate_job_id, fate_flow_path)

    return ok_response(data=stdout)


@bp.route('/get_model_params', methods=['POST'])
def get_model_param():
    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()
    fate_job_id = data.get('fate_job_id')
    party_id = data.get('party_id')
    role = data.get('role')
    cpn = data.get('cpn')
    fate_flow_path = current_app.config['FATE_FLOW_PATH']
    stdout = get_model(fate_job_id, party_id, role, cpn, fate_flow_path)

    return ok_response(data=stdout)


@bp.route('/infer', methods=['POST'])
def infer_with_model():
    if not request.data:
        return error_response(message="None data.")
    data = request.get_json()
    data_sql = data.get('data_sql')
    model_params = data.get('model_params')

    # Get data
    # 没有sql语句
    if not data_sql:
        return error_response(message="None data_sql in request.")

    db = get_db()
    db_data = None
    try:
        db_data = db.execute(r'''{}'''.format(data_sql)).fetchall()
    except Exception as e:
        return error_response(message="Query data from database error. Error info: " + str(e))

    if (len(db_data) == 0):
        return error_response(message="没有满足条件的数据")

    table_head = len(db_data[0])
    if (table_head < 2):
        return error_response(message="数据缺少id或者属性")

    tmp_path = current_app.config['TEMP_DATA_DIR']

    _, file_path = generate_csv(db_data=db_data, tmp_path=tmp_path)
    data_frame = get_dataframe(file_path)

    # Predict
    # Return result 
    