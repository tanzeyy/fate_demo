import os
import json

HOME_DIR = os.path.split(os.path.realpath(__file__))[0]
TRAIN_TEMPLATE = HOME_DIR + "/templates/train_homo_lr_job_conf.json"


def generate_train_info(param):
    with open(TRAIN_TEMPLATE, 'r', encoding='utf-8') as f:
        conf_json = json.loads(f.read())


if __name__ == '__main__':
    print(TRAIN_TEMPLATE)