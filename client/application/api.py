from flask import Blueprint, jsonify, make_response, request, current_app
from .utils import ok_response, error_response, upload_json, exec_upload_task, get_timeid, exec_modeling_task, job_status_checker, get_model, generate_csv, get_dataframe, homo_lr_predict
from .db import get_db, get_db_engine
import time
import csv
import json
import os
import pandas as pd
from sklearn.preprocessing import RobustScaler

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

    data_sql = data.get('data_sql')
    attributes = data.get('attributes')
    label_value = data.get('label_value')

    # 没有sql语句
    if not data_sql:
        return error_response(message="None data_sql in request.")

    # 没有attributes
    if not attributes or type(attributes) is not list:
        return error_response(message="None attributes in request, or attributes is not a array.")

    db_engine = get_db_engine()
    try:
        df_list = []
        for sql in data_sql.values():
            df_list.append(pd.read_sql(sql, con=db_engine).fillna(0))
        df = pd.concat(df_list)
        attribute_data = df[attributes[1:-1]].astype('float64')
        label_data = df[attributes[-1]].astype('int')
        db_data = pd.concat([df[attributes[0]], attribute_data, label_data], axis=1)
        label_name = attributes[-1]
        db_data[label_name].replace(label_value, 1, inplace=True)
        db_data.loc[db_data[label_name] != 1, label_name] = 0
        db_data[attributes[1:-1]] = RobustScaler().fit_transform(db_data[attributes[1:-1]])
    except Exception as e:
        print(str(e))
        return error_response(message="Query data from database error. Error info: " + str(e))

    # if (len(db_data) == 0):
    #     return error_response(message="没有满足条件的数据")

    tmp_path = current_app.config['TEMP_DATA_DIR']

    prefix, file_path = generate_csv(db_data=db_data, tmp_path=tmp_path)

    template = current_app.config['UPLOAD_TEMPLATE']
    conf_json = upload_json(file_path, prefix, template)
    fate_flow_path = current_app.config['FATE_FLOW_PATH']

    stdout = exec_upload_task(conf_json, "", fate_flow_path)
    info = {"data_volum":len(df)}
    return ok_response(data=stdout, info=info)


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
    attributes = data.get('attributes')
    unique_id = data.get('unique_id')

    # Get data
    # 没有sql语句
    if not data_sql:
        return error_response(message="None data_sql in request.")

    if not model_params:
        return error_response(message="None model_params in request.")

    # 没有attributes
    if not attributes or type(attributes) is not list:
        return error_response(message="None attributes in request, or attributes is not a array.")

    if not unique_id:
        return error_response(message="None unique_id in request.")

    db_engine = get_db_engine()
    try:
        df = pd.read_sql(data_sql, con=db_engine, coerce_float=True)
        db_data = df[attributes]
    except Exception as e:
        return error_response(message="Query data from database error. Error info: " + str(e))

    if (len(db_data) == 0):
        return error_response(message="没有满足条件的数据")

    # Predict
    try:
        results = homo_lr_predict(db_data.astype('float64'), model_params).to_frame(name='label')
        results[unique_id] = df[unique_id]
        outputs = results.to_dict("records")
    except:
        return error_response(message="Infer task failed, please check your input data or the model.")

    return ok_response(data=outputs)
    