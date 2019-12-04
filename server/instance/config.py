import os
SQLALCHEMY_DATABASE_URI="mysql+pymysql://fl:123@192.168.23.103:3306/app"
SUBMIT_DATA_URI="{}/api/read_data"
INSTANCE_DIR = os.path.split(os.path.realpath(__file__))[0]
TRAIN_TEMPLATE = INSTANCE_DIR + "/../application/templates/train_homo_lr_job_conf.json"
LR_DSL_TEMPLATE = INSTANCE_DIR + "/../application/templates/train_homo_lr_job_dsl.json"

# Celery-Backend
CELERY_RESULT_BACKEND="redis://192.168.25.105:6380"
CELERY_BROKER_URL="redis://192.168.25.105:6380"
