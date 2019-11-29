import requests
from multiprocessing import Pool

from flask import Blueprint, jsonify, make_response, request, current_app
from .libs.utils import ok_response, error_response
from .libs.db import get_db
from .libs.models import User, Model, Order

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
    data_info = data.get('input_data')

    db = get_db()

    # Submit data
    def submit_data(url, data):
        requests.post(url, json=data)

    responses = {}
    p = Pool(len(data_info))
    for k, v in data_info.items():
        user = db.query(User).filter(User.id==k).first()
        url = user.client_url
        responses[user.party_id] = p.apply_async(submit_data, args=(url, v))
    p.close()
    p.join()
    # Generate config file
    




    
    return make_response(jsonify(code=200, message='fate demo'), 200)
