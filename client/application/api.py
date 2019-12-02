from flask import Blueprint, jsonify, make_response, request, current_app
from .utils import ok_response, error_response, upload_json, exec_upload_task, get_timeid, exec_modeling_task, job_status_checker
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
    head = ['x' + str(i) for i in range(table_head-2)]

    tmp_path = current_app.config['TEMP_DATA_DIR']
    try:
        os.makedirs(tmp_path)
    except:
        pass

    prefix = get_timeid()
    file_path = os.path.join(tmp_path, prefix + '.csv')

    with open(file_path, "w") as csvfile:
        writer = csv.writer(csvfile)
        # 先写入columns_name
        row = ["x", "y"]
        row.extend(head)
        writer.writerow(row)
        # 写入多行用writerows
        writer.writerows(db_data)

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