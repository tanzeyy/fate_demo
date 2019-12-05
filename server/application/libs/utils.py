import requests
from flask import jsonify, make_response


def ok_response(message=None, data=None):
    return make_response(jsonify(code=200, message=message, data=data), 200)


def error_response(message=None):
    return make_response(jsonify(code=400, message=message), 200)


def redirect_response(url=None):
    return make_response(jsonify(code=302, url=url), 200)


# Submit data
def submit_data(url, data_sql, attributes, label_value):
    return requests.post(url, json={"data_sql": data_sql, "attributes": attributes, "label_value": label_value})

# Submit train task
def submit_train_task(url, conf, dsl):
    return requests.post(url, json={'config_dict': conf, 'dsl_dict': dsl})
    
# Request job status
def check_job_status(url, fate_job_id):
    return requests.post(url, json={'fate_job_id': fate_job_id})

# Request model infer
def submit_infer_task(url, data_sql, model_params, attributes, unique_id):
    data = {'data_sql':data_sql, 'model_params':model_params, 'attributes':attributes, 'unique_id':unique_id}
    print(data)
    return requests.post(url, json=data)

def query_model_params(url, fate_job_id, party_id, role, cpn):
    data = {'fate_job_id':fate_job_id, 'party_id':party_id, 'role': role, 'cpn':cpn}
    print(data)
    return requests.post(url, json=data)