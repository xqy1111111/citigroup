# 将target文件夹中的所有xlsx文件转换为固定的json文件

import time
import os
import pandas as pd
import json

def translate(value):
    switch={
       "本次交易": "current_transaction",
       "相关交易": "related_transactions",
       "操作信息": "operation_information",
       "初始账户": "initial_account",
       "目标账户": "target_account",
       "欺诈检测": "fraud_detection"
    }
    return switch.get(value, value)



def process_target_to_json(target_dir=None,json_dir=None):
    # 首先，获取本文件的路径
    current_path = os.path.abspath(__file__)
    print(f"本文件的路径是: {current_path}\n")
    # 然后相对于本文件的路径
    base_path = os.path.dirname(current_path)
   
    target_path = target_dir if target_dir else  os.path.join(base_path, "DataStructuring", "DataStructuring", "TargetData")
    json_path =json_dir if json_dir else os.path.join(base_path, "DataStructuring", "DataStructuring", "JsonData")
    print(f"目标文件夹的绝对路径是: {target_path}")

    # 然后，遍历target文件夹中的所有xlsx文件
    for file in os.listdir(target_path):
        if file.endswith(".xlsx"):
            # 读取xlsx文件
            df = pd.read_excel(os.path.join(target_path, file))
            
            # 初始化结果字典
            result = {}
            current_category = None
            
            # 遍历每一行数据
            for _, row in df.iterrows():

                #time.sleep(2)#用来理解一下处理逻辑
                #print("\n\n\n")
                #print(_)
                #print(row)
                #print("\n\n\n")
                category = row.iloc[0]
                category=translate(category)
                key = row.iloc[1]
                value = row.iloc[2]
                
                # 如果category不为空，更新当前category
                if pd.notna(category):
                    current_category = category
                    result[current_category] = []
                
                # 如果有当前category，添加key-value对
                if current_category is not None:
                    result[current_category].append({
                        "key": str(key),
                        "value": str(value)
                    })
            
            # 保存为JSON文件
            output_filename = os.path.splitext(file)[0] + '.json'
            output_path = os.path.join(json_path, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            print(f"已将 {file} 转换为 {output_filename}")











