from flask import jsonify, make_response


def ok_response(message=None, data=None):
    return make_response(jsonify(code=200, message=message, data=data), 200)


def error_response(message=None):
    return make_response(jsonify(code=400, message=message), 200)


def redirect_response(url=None):
    return make_response(jsonify(code=302, url=url), 200)


def exec_upload_task(config_dict, role, fate_flow_path):
    prefix = '_'.join(['upload', role])
    config_path = save_config_file(config_dict=config_dict, prefix=prefix)

    subp = subprocess.Popen(["python",
                             FATE_FLOW_PATH,
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


def upload_json(file_path, name):
    UPLOAD_TEMPLATE = current_app.config['UPLOAD_TEMPLATE']
    with open(UPLOAD_TEMPLATE, 'r', encoding='utf-8') as f:
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


def save_config_file(config_dict, prefix):
    config = json.dumps(config_dict)
    config_path = gen_unique_path(prefix)
    config_dir_path = os.path.dirname(config_path)
    os.makedirs(config_dir_path, exist_ok=True)
    with open(config_path, "w") as fout:
        # print("path:{}".format(config_path))
        fout.write(config + "\n")
    return config_path


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
    with open(LATEST_TRAINED_RESULT, 'w') as outfile:
        json.dump(stdout, outfile)

    status = stdout["retcode"]
    if status != 0:
        raise ValueError(
            "[Trainning Task]exec fail, status:{}, stdout:{}".format(status, stdout))
    return stdout


def job_status_checker(jobid):
    # check_counter = 0
    # while True:
    subp = subprocess.Popen(["python",
                             FATE_FLOW_PATH,
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


def wait_query_job(jobid):
    start = time.time()
    while True:
        job_status = job_status_checker(jobid)
        if job_status == SUCCESS:
            print("Task Finished")
            break
        elif job_status == FAIL:
            print("Task Failed")
            break
        else:
            time.sleep(RETRY_JOB_STATUS_TIME)
            end = time.time()
            print("Task is running, wait time: {}".format(end - start))

            if end - start > MAX_WAIT_TIME:
                print("Task Failed, may by stuck in federation")
                break


def submit_job():
    with open(DSL_PATH, 'r', encoding='utf-8') as f:
        dsl_json = json.loads(f.read())

    with open(SUBMIT_CONF_PATH, 'r', encoding='utf-8') as f:
        conf_json = json.loads(f.read())

    conf_json['job_parameters']['work_mode'] = WORK_MODE

    conf_json['initiator']['party_id'] = GUEST_ID
    conf_json['role']['guest'] = [GUEST_ID]
    conf_json['role']['host'] = [HOST_ID]
    conf_json['role']['arbiter'] = [ARBITER_ID]

    guest_table_name, guest_namespace = generate_data_info(GUEST)
    host_table_name, host_namespace = generate_data_info(HOST)

    conf_json['role_parameters']['guest']['args']['data']['train_data'] = [
        {
            'name': guest_table_name,
            'namespace': guest_namespace
        }
    ]
    conf_json['role_parameters']['host']['args']['data']['train_data'] = [
        {
            'name': host_table_name,
            'namespace': host_namespace
        }
    ]

    # print("Submit job config json: {}".format(conf_json))
    stdout = exec_modeling_task(dsl_json, conf_json)
    job_id = stdout['jobId']
    fate_board_url = stdout['data']['board_url']
    print("Please check your task in fate-board, url is : {}".format(fate_board_url))
    log_path = HOME_DIR + '/../../logs/{}'.format(job_id)
    print("The log info is located in {}".format(log_path))
    wait_query_job(job_id)


def predict_task():
    try:
        with open(LATEST_TRAINED_RESULT, 'r', encoding='utf-8') as f:
            model_info = json.loads(f.read())
    except FileNotFoundError:
        raise FileNotFoundError('Train Result not Found, please finish a train task before going to predict task')

    model_id = model_info['data']['model_info']['model_id']
    model_version = model_info['data']['model_info']['model_version']

    with open(TEST_PREDICT_CONF, 'r', encoding='utf-8') as f:
        predict_conf = json.loads(f.read())

    predict_conf['initiator']['party_id'] = GUEST_ID
    predict_conf['job_parameters']['work_mode'] = WORK_MODE
    predict_conf['job_parameters']['model_id'] = model_id
    predict_conf['job_parameters']['model_version'] = model_version

    predict_conf['role']['guest'] = [GUEST_ID]
    predict_conf['role']['host'] = [HOST_ID]
    predict_conf['role']['arbiter'] = [ARBITER_ID]

    guest_table_name, guest_namespace = generate_data_info(GUEST)
    host_table_name, host_namespace = generate_data_info(HOST)

    predict_conf['role_parameters']['guest']['args']['data']['eval_data'] = [
        {
            'name': guest_table_name,
            'namespace': guest_namespace
        }
    ]

    predict_conf['role_parameters']['host']['args']['data']['eval_data'] = [
        {
            'name': host_table_name,
            'namespace': host_namespace
        }
    ]

    predict_conf_path = save_config_file(predict_conf, 'predict_conf')
    subp = subprocess.Popen(["python",
                             FATE_FLOW_PATH,
                             "-f",
                             "submit_job",
                             "-c",
                             predict_conf_path
                             ],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    stdout, stderr = subp.communicate()
    stdout = stdout.decode("utf-8")
    print("stdout:" + str(stdout))
    stdout = json.loads(stdout)
    status = stdout["retcode"]
    job_id = stdout['jobId']
    wait_query_job(job_id)
    if status != 0:
        raise ValueError(
            "[Upload task]exec fail, status:{}, stdout:{}".format(status, stdout))
    return stdout

