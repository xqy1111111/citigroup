# 将target文件夹中的所有xlsx文件转换为固定的json文件

import os
import pandas as pd
import json

def process_target_to_json():
    # 首先，获取本文件的路径
    current_path = os.path.abspath(__file__)
    print(f"本文件的路径是: {current_path}\n")
    # 然后相对于本文件的路径
    target_path = os.path.join(current_path, "../DataStructuring/DataStructuring/TargetData")
    json_path = os.path.join(current_path, "../DataStructuring/DataStructuring/JsonData")
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
                category = row.iloc[0]
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











