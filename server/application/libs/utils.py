import requests
from flask import jsonify, make_response


def ok_response(message=None, data=None):
    return make_response(jsonify(code=200, message=message, data=data), 200)


def error_response(message=None):
    return make_response(jsonify(code=400, message=message), 200)


def redirect_response(url=None):
    return make_response(jsonify(code=302, url=url), 200)


# Submit data
def submit_data(url, data_sql, attributes):
    return requests.post(url, json={"data_sql": data_sql, "attributes": attributes})

# Submit train task
def submit_train_task(url, conf, dsl):
    return requests.post(url, json={'config_dict': conf, 'dsl_dict': dsl})
    
# Request job status
def check_job_status(url, fate_job_id):
    return requests.post(url, json={'fate_job_id': fate_job_id})