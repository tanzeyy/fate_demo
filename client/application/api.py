from flask import Blueprint, jsonify, make_response, request, current_app
from .utils import ok_response, error_response
from .db import get_db
import time
import csv
import json
import os

bp = Blueprint('data', __name__, url_prefix='/data')

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
        return error_response(message="Query data from databse error. Error info: " + str(e))

    if (len(db_data) == 0):
        return error_response(message="没有满足条件的数据")

    table_head = len(db_data[0])
    if (table_head < 2):
        return error_response(message="数据缺少id或者标签")
    head = ['x' + str(i) for i in range(table_head-2)]

    file_path = current_app.config['TEMP_DATA_DIR']
    try:
        os.makedirs(file_path)
    except:
        pass

    current_milli_time = lambda: str(round(time.time() * 1000))
    prefix = current_milli_time()
    file_path = file_path + prefix + '.csv'

    with open(file_path, "w") as csvfile:
        writer = csv.writer(csvfile)
        # 先写入columns_name
        row = ["x", "y"]
        row.extend(head)
        writer.writerow(row)
        # 写入多行用writerows
        writer.writerows(db_data)

    upload_json(file_path, prefix)

    # TODO: 发给fate
    return ok_response(message="ok")


def upload_json(file_path, name):
    UPLOAD_TEMPLATE = current_app.config['UPLOAD_TEMPLATE']
    with open(UPLOAD_TEMPLATE, 'r', encoding='utf-8') as f:
        conf_json = json.loads(f.read())
        conf_json['file'] = file_path
        conf_json['table_name'] = name
        conf_json['namespace'] = name
    print(conf_json)