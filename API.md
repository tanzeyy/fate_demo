[TOC]

### 服务器信息

| 服务器地址     | user_id | name | role           | 数据                        |
| :------------- | ------- | ---- | -------------- | --------------------------- |
| 192.168.25.105 | 1       | 暂无 | 联邦学习服务端 |                             |
| 192.168.25.106 | 2       | 暂无 | 客户机         | 苏州市立医院(suzhou-szslyy) |
| 192.168.25.107 | 3       | 暂无 | 客户机         | 浙大儿院(zhejiang-zdey)     |
| 192.168.25.108 | 4       | 暂无 | 客户机         | 西北妇幼保健院(shanxi-xbfy) |



### 模型训练

- 请求地址：`http://192.168.25.105:5000/model/train`

- 请求方式：`POST`

- 请求参数：

  ```json
  {
   "user_id": 3,
   "model_type": "lr",
   "model_params": {
    "penalty": "L2",
    "optimizer": "sgd",
    "eps": 1e-4,
    "alpha": 0.01,
    "max_iter": 5,
    "converge_func": "diff",
    "batch_size": 500,
    "learning_rate": 0.15,
    "decay": 1,
    "decay_sqrt": true,
    "init_param": {
     "init_method": "zeros"
    },
    "encrypt_param": {
     "method": "Paillier"
    },
    "cv_param": {
     "need_cv": false
    }
   },
   "party_id": [4, 2],
   "data_info": {
    "2": {
     "pos": "select * from data.blooddata_small;",
     "neg": "select * from data.blooddata_small;"
    },
    "3": {
     "pos": "select * from data.blooddata_small;",
     "neg": "select * from data.blooddata_small;"
    },
    "4": {
     "pos": "select * from data.blooddata_small;",
     "neg": "select * from data.blooddata_small;"
    }
   },
   "unique_id": "unique_id",
   "attributes": ["C6", "C6DC", "C8"],
   "label_name": "diagnosis",
   "label_value": 38
  }
  ```

- 请求成功返回：

  ```json
  {
      "code": 200,
      "data": {
          "model_id": 137,
          "order_id": 169
      },
      "message": null
  }
  ```
  
  

### 模型训练进度查询

- 请求地址：`http://192.168.25.105:5000/model/train_status`

- 请求方式：`GET`

- 请求参数：`order_id=169`

- 请求成功返回：

  ```json
{
      "code": 200,
      "data": {
          "data_volum": {
              "2": 592,
              "3": 702,
              "4": 554
          },
          "model_id": 137,
          "train_status": {
              "current_tasks": "[\"2019121614323335921220_dataio_0\"]",
              "train_progress": 33,
              "train_status": "running"
          }
      },
      "message": null
  }
  ```
  



### 模型信息查询

- 请求地址：`http://192.168.25.105:5000/model/info`

- 请求方式：`GET`

- 请求参数：`model_id=137`

- 请求成功返回：

  ```json
  {
      "code": 200,
      "data": {
          "data_volum": {
              "2": 592,
              "3": 702,
              "4": 554
          },
          "model_params": {
              "alpha": 0.01,
              "attributes": [
                  "C6",
                  "C6DC",
                  "C8"
              ],
              "batch_size": 500,
              "converge_func": "diff",
              "cv_param": {
                  "need_cv": false
              },
              "decay": 1,
              "decay_sqrt": true,
              "encrypt_param": {
                  "method": "Paillier"
              },
              "eps": 0.0001,
              "init_param": {
                  "init_method": "zeros"
              },
              "label_name": "diagnosis",
              "learning_rate": 0.15,
              "max_iter": 5,
              "optimizer": "sgd",
              "penalty": "L2",
              "unique_id": "unique_id"
          },
          "model_type": "Logistic Regression",
          "party_id": [
              4,
              2
          ],
          "user_id": 3
      },
      "message": null
  }
  ```
  
  

### 模型使用

- 请求地址：`http://192.168.25.105:5000/model/infer`

- 请求方式：`POST`

- 请求参数：

  ```json
  {
  	"model_id": "137",
  	"input_data": {
  		"user_id": "4",
  		"data_sql": "SELECT * FROM select * from data.blooddata_small;"
  	}
  }
  ```

- 请求成功返回：

  ```json
  {
      "code": 200,
      "data": {
          "order_id": 176
      },
      "message": null
  }
  ```

  

### 计算进度查询

- 请求地址：`http://192.168.25.105:5000/model/infer_status`

- 请求方式：`GET`

- 请求参数：`order_id=170`

- 请求成功返回：

  ```json
  {
      "code": 200,
      "data": {
          "infer_status": "finished",
          "result": [
              {
                  "label": 0.0768,
                  "unique_id": "1"
              }
          ]
      },
      "message": null
  }
  ```

### 训练状态地址

- 请求地址：`http://192.168.25.105:5000/model/board_url`

- 请求方式：`GET`

- 请求参数：`order_id=169`

- 请求成功返回：
  ```json
{
      "code": 200,
      "data": {
          "board_url": {
              "2": "http://192.168.25.106:8080/#/dashboard?job_id=2019121614323335921220&role=host&party_id=9999",
              "3": "http://192.168.25.107:8080/#/dashboard?job_id=2019121614323335921220&role=guest&party_id=9998",
              "4": "http://192.168.25.108:8080/#/dashboard?job_id=2019121614323335921220&role=host&party_id=9997"
          }
      },
      "message": null
}
  ```
