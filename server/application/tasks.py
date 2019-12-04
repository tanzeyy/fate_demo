import json
import requests

from . import celery

from .libs.db import get_db
from .libs.models import Order


@celery.task
def infer_task(url, data_sql, model_params, attributes, unique_id, order_id):
    data = {'data_sql': data_sql, 'model_params': model_params,
            'attributes': attributes, 'unique_id': unique_id}
    print(data)
    response = requests.post(url, json=data)

    db = get_db()
    order = db.query(Order).filter(Order.id==order_id).first()
    job_info = json.loads(order.job_info)
    job_info['infer_status'] = 'finished'
    job_info['result'] = json.loads(response.text)['data']

    order.job_info = json.dumps(job_info)

    db.add(order)
    db.commit()

    return job_info
