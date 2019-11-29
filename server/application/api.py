from flask import Blueprint, jsonify, make_response
from .libs.utils import ok_response, error_response

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/test', methods=['GET', ])
def test():
    return make_response(jsonify(code=200, message='fate demo'), 200)

@bp.route('/train/generator', methods=['POST'])
def generator():
    pass