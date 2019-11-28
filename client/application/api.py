from flask import Blueprint, jsonify, make_response
from .utils import ok_response, error_response

bp = Blueprint('data', __name__, url_prefix='/data')

@bp.route('/read_data', methods=['POST'])
def read_data():
    '''
    根据sql语句读取数据
    生成csv
    '''


    return make_response(jsonify(code=200, message='fate demo'), 200)

@bp.route('/train/generator', methods=['POST'])
def generator():
    pass