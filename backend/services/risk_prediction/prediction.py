import pandas as pd
import numpy as np
from sklearn.ensemble import AdaBoostClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

train_columns = {}
class AdaBoostPredicModel:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # print(current_dir)
        self.model = joblib.load(os.path.join(current_dir, 'adaboost_model.joblib'))

    def TrainandPred(self,X0):
        y_pred = self.model.predict(X0)
        y_pred_proba0 = self.model.predict_proba(X0)[:, 0]
        y_pred_proba = self.model.predict_proba(X0)[:, 1]
        # result =  {
        #     "predict": y_pred.tolist(),
        #     "probability of predict as 0": y_pred_proba0.tolist(),
        #     "probability of predict as 1": y_pred_proba.tolist(),
        # }
        result = y_pred_proba[0]
        print("probability of predict as 1:", result)
        return result


from flask import request, jsonify
import openpyxl

model = AdaBoostPredicModel()

def predict_once(file_path):
    # 获取上传的文件
    # 将文件内容读取为字符串
    df = pd.read_excel(file_path, engine='openpyxl', nrows=11)
    for i in range(0, 11):
        if i != 1 and i != 2 and i != 9 and i != 10:
            df = df.drop(index=i)
    columns = ['交易类型', '交易金额', '初始账户旧余额', '初始账户新余额']
    data = pd.DataFrame(
        columns=['amount', 'oldbalanceOrg', 'newbalanceOrig', 'type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT',
                 'type_PAYMENT', 'type_TRANSFER'])
    for key in columns:
        # 找到包含特定条目的行
        mask = df['表头中具体条目'] == key
        if mask.any():
            content = df.loc[mask, '内容'].iloc[0]
            if key == '交易类型':
                if content == '入账':
                    data.loc[0, 'type_CASH_IN'] = True
                    data.loc[0, 'type_CASH_OUT'] = False
                    data.loc[0, 'type_DEBIT'] = False
                    data.loc[0, 'type_PAYMENT'] = False
                    data.loc[0, 'type_TRANSFER'] = False
                elif content == '提现':
                    data.loc[0, 'type_CASH_IN'] = False
                    data.loc[0, 'type_CASH_OUT'] = True
                    data.loc[0, 'type_DEBIT'] = False
                    data.loc[0, 'type_PAYMENT'] = False
                    data.loc[0, 'type_TRANSFER'] = False
                elif content == '借记':
                    data.loc[0, 'type_CASH_IN'] = False
                    data.loc[0, 'type_CASH_OUT'] = False
                    data.loc[0, 'type_DEBIT'] = True
                    data.loc[0, 'type_PAYMENT'] = False
                    data.loc[0, 'type_TRANSFER'] = False
                elif content == '支付':
                    data.loc[0, 'type_CASH_IN'] = False
                    data.loc[0, 'type_CASH_OUT'] = False
                    data.loc[0, 'type_DEBIT'] = False
                    data.loc[0, 'type_PAYMENT'] = True
                    data.loc[0, 'type_TRANSFER'] = False
                elif content == '转账':
                    data.loc[0, 'type_CASH_IN'] = False
                    data.loc[0, 'type_CASH_OUT'] = False
                    data.loc[0, 'type_DEBIT'] = False
                    data.loc[0, 'type_PAYMENT'] = False
                    data.loc[0, 'type_TRANSFER'] = True
                elif content == '无':
                    print("error:交易数据不足")
                    return
                else:
                    print("error:交易类型错误")
                    return
            elif key == '交易金额':
                if content == '无':
                    print("error:交易数据不足")
                    return
                else:
                    data.loc[0, 'amount'] = content
            elif key == '初始账户旧余额':
                if content == '无':
                    print("error:交易数据不足")
                    return
                else:
                    data.loc[0, 'oldbalanceOrg'] = content
            elif key == '初始账户新余额':
                if content == '无':
                    print("error:交易数据不足")
                    return
                else:
                    data.loc[0, 'newbalanceOrig'] = content
        else:
            # 如果没有找到特定条目，添加空值
            data[key] = [None]

    # 训练模型并预测

    results = model.TrainandPred(data)
    return results

#示例操作调用函数

def predict_all():
    dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './SourceData')
    file_list = os.listdir(dir_path)
    results = {}
    for file in file_list:
        file_path = os.path.join(dir_path, file)
        # 如果是excel文件，则预测
        if file.endswith('.xlsx'):
            results[file] = predict_once(file_path)
    return results

# print(predict_all(dir_path))