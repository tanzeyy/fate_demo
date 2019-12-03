### 服务器

| 服务器地址     | user_id | name | role           | 数据                        |
| :------------- | ------- | ---- | -------------- | --------------------------- |
| 192.168.25.105 | 1       | 暂无 | 联邦学习服务端 |                             |
| 192.168.25.106 | 2       | 暂无 | 客户机         | 苏州市立医院(suzhou-szslyy) |
| 192.168.25.107 | 3       | 暂无 | 客户机         | 浙大儿院(zhejiang-zdey)     |
| 192.168.25.108 | 4       | 暂无 | 客户机         | 西北妇幼保健院(shanxi-xbfy) |



### 模型训练订单提交

- 请求地址：`http://192.168.25.105:5000/model/train`

- 请求方式：`POST`

- 请求参数：

  ```json
  {
  	 "user_id": 4, 
  	 "model_type": "lr",
  	 "model_params": {
  	        "penalty": "L2",
  	        "optimizer": "sgd",
  	        "eps": 1e-4,
  	        "alpha": 0.01,
  	        "max_iter": 30,
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
  	    "party_id": [2, 3],
  	    "data_info": {
  	     "4": "SELECT * FROM data.breast_homo_guest;",
  	     "2": "SELECT * FROM data.breast_homo_host;",
  	     "3": "SELECT * FROM data.breast_homo_host;"
  	    }
      
  }
  ```

- 请求成功返回：

  ```json
  {
      "code": 200,
      "data": {
          "model_id": 9,
          "order_id": 9
      },
      "message": null
  }
  ```

  

### 模型训练进度查询

- 请求地址：`http://192.168.25.105:5000/model/train_status`

- 请求方式：`GET`

- 请求参数：`order_id=15`

- 请求成功返回：

  ```json
  {
      "code": 200,
      "data": {
          "model_id": 15,
          "train_status": "running"
      },
      "message": null
  }
  ```
  


