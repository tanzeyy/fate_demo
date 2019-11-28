from flask import Blueprint, jsonify, make_response
from .utils import ok_response, error_response, redirect_response

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/test', methods=['GET', ])
def test():
    return ok_response(message='fate demo')