import os

SQLALCHEMY_DATABASE_URI="mysql+pymysql://fl:123@127.0.0.1:3307/data"

INSTANCE_DIR = os.path.split(os.path.realpath(__file__))[0]
TEMP_DATA_DIR = '/tmp/fate_data/'
UPLOAD_TEMPLATE = INSTANCE_DIR + "/../application/templates/upload_data.json"
FATE_FLOW_PATH = '/data/projects/fate/python/fate_flow/fate_flow_client.py'