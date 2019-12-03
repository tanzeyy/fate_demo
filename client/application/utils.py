from flask import jsonify, make_response, current_app
import subprocess
import json
import os
import time
import random
import sys
import traceback
import csv
import pandas as pd

HOME_DIR = os.path.split(os.path.realpath(__file__))[0]
SUCCESS = 'success'
RUNNING = 'running'
FAIL = 'failed'

def ok_response(message=None, data=None):
    return make_response(jsonify(code=200, message=message, data=data), 200)


def error_response(message=None):
    return make_response(jsonify(code=400, message=message), 200)


def redirect_response(url=None):
    return make_response(jsonify(code=302, url=url), 200)


def homo_lr_predict(df, params):
    bias = params['data']['data']['intercept']
    weights_dict = params['data']['data']['weight']
    weights = pd.DataFrame(weights_dict, index=df.index)
    return 1 / (1 + np.exp(- ((df * weights).sum(axis=1) + bias)))


def exec_upload_task(config_dict, fate_flow_path):
    prefix = "upload"
    config_path = save_config_file(config_dict=config_dict, prefix=prefix)

    subp = subprocess.Popen(["python",
                             fate_flow_path,
                             "-f",
                             "upload",
                             "-c",
                             config_path],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    stdout, stderr = subp.communicate()
    stdout = stdout.decode("utf-8")
    print("stdout:" + str(stdout))
    stdout = json.loads(stdout)
    status = stdout["retcode"]
    if status != 0:
        raise ValueError(
            "[Upload task]exec fail, status:{}, stdout:{}".format(status, stdout))
    return stdout


def save_config_file(config_dict, prefix):
    config = json.dumps(config_dict)
    config_path = gen_unique_path(prefix)
    config_dir_path = os.path.dirname(config_path)
    os.makedirs(config_dir_path, exist_ok=True)
    with open(config_path, "w") as fout:
        # print("path:{}".format(config_path))
        fout.write(config + "\n")
    return config_path


def upload_json(file_path, name, template):
    with open(template, 'r', encoding='utf-8') as f:
        conf_json = json.loads(f.read())
        conf_json['file'] = file_path
        conf_json['table_name'] = name
        conf_json['namespace'] = name
    return conf_json


def get_timeid():
    return str(int(time.time())) + "_" + str(random.randint(1000, 9999))


def gen_unique_path(prefix):
    return HOME_DIR + "/user_config/" + prefix + ".config_" + get_timeid()


def prettify(response, verbose=True):
    if verbose:
        print(json.dumps(response, indent=4))
        print()
    return response


def exec_upload_task(config_dict, role, fate_flow_path):
    prefix = '_'.join(['upload', role])
    config_path = save_config_file(config_dict=config_dict, prefix=prefix)

    subp = subprocess.Popen(["python",
                             fate_flow_path,
                             "-f",
                             "upload",
                             "-c",
                             config_path],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    stdout, stderr = subp.communicate()
    stdout = stdout.decode("utf-8")
    print("stdout:" + str(stdout))
    stdout = json.loads(stdout)
    status = stdout["retcode"]
    if status != 0:
        raise ValueError(
            "[Upload task]exec fail, status:{}, stdout:{}".format(status, stdout))
    return stdout


def exec_modeling_task(dsl_dict, config_dict, fate_flow_path):
    dsl_path = save_config_file(dsl_dict, 'train_dsl')
    conf_path = save_config_file(config_dict, 'train_conf')
    print("dsl_path: {}, conf_path: {}".format(dsl_path, conf_path))
    subp = subprocess.Popen(["python",
                             fate_flow_path,
                             "-f",
                             "submit_job",
                             "-c",
                             conf_path,
                             "-d",
                             dsl_path
                             ],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    stdout, stderr = subp.communicate()
    stdout = stdout.decode("utf-8")
    print("stdout:" + str(stdout))
    stdout = json.loads(stdout)
    status = stdout["retcode"]
    if status != 0:
        raise ValueError(
            "[Trainning Task]exec fail, status:{}, stdout:{}".format(status, stdout))
    return stdout


def job_status_checker(jobid, fate_flow_path):
    # check_counter = 0
    # while True:
    subp = subprocess.Popen(["python",
                             fate_flow_path,
                             "-f",
                             "query_job",
                             "-j",
                             jobid
                             ],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    stdout, stderr = subp.communicate()
    stdout = stdout.decode("utf-8")
    stdout = json.loads(stdout)
    status = stdout["retcode"]
    if status != 0:
        return RUNNING
    check_data = stdout["data"]
    task_status = []

    for component_stats in check_data:
        status = component_stats['f_status']
        task_status.append(status)

    if any([s == FAIL for s in task_status]):
        return FAIL

    if any([s == RUNNING for s in task_status]):
        return RUNNING

    return SUCCESS


def get_model(jobid, party_id, role, cpn, fate_flow_path):
    subp = subprocess.Popen(["python",
                             fate_flow_path,
                             "-f",
                             "component_output_model",
                             "-j",
                             jobid,
                             "-p",
                             party_id,
                             "-r",
                             role,
                             "-cpn",
                             cpn
                             ],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    stdout, stderr = subp.communicate()
    stdout = stdout.decode("utf-8")
    print("stdout:" + str(stdout))
    stdout = json.loads(stdout)
    status = stdout["retcode"]
    if status != 0:
        raise ValueError(
            "[Task]exec fail, status:{}, stdout:{}".format(status, stdout))
    return stdout


def generate_csv(db_data, tmp_path):
    try:
        os.makedirs(tmp_path)
    except:
        pass

    prefix = get_timeid()
    file_path = os.path.join(tmp_path, prefix + '.csv')

    table_head = len(db_data[0])
    head = ['x' + str(i) for i in range(table_head - 2)]

    with open(file_path, "w") as csvfile:
        writer = csv.writer(csvfile)
        # 先写入columns_name
        row = ["x", "y"]
        row.extend(head)
        writer.writerow(row)
        # 写入多行用writerows
        writer.writerows(db_data)

    return prefix, file_path

def get_dataframe(file_path):
    file = pd.read_csv(file_path)
    dataframe = pd.DataFrame(file)
    return dataframe
