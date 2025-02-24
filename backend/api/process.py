from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from models.chat import ChatHistory, Message


from services.ai_service import AIService
from services.DataStructuring.DataStructuring import main_process
from services import target_to_json
import shutil
import os
import platform
import glob
import json
from io import BytesIO

from ._file import download_file
router = APIRouter()


@router.post("/{file_id}/process")
async def process_file_to_json(file_id: str):
    """
    处理文件并返回json数据
    """
    file_data = download_file(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    filename, file_content = file_data



   
    
    current_file_path = os.path.abspath(__file__)
    # 获得当前文件的父目录
    parent_dir = os.path.dirname(current_file_path)
    parent_dir = os.path.dirname(parent_dir)
    upload_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "SourceData")
    excel_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "TargetData")
    json_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "JsonData")

    # 如果文件夹不存在就新建文件夹
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)
    print("\n\n\n")
    print(upload_folder)
    print("\n\n\n")
    '''
        # 获得当前文件路径
        current_file_path = os.path.abspath(__file__)
        # 获得当前文件的父目录
        parent_dir = os.path.dirname(current_file_path)
        parent_dir = os.path.dirname(parent_dir)
        upload_folder = os.path.join("..", parent_dir, "services", "DataStructuring", "DataStructuring", "SourceData")
        json_folder = os.path.join("..", parent_dir, "services", "DataStructuring", "DataStructuring", "JsonData")
    '''
    file_path = os.path.join(upload_folder, filename)
    # print("\n***file_path: ", file_path)
    
    # 删除file_path 下的所有文件
    if os.path.exists(upload_folder):
        for file_name_ in os.listdir(upload_folder):
            os.remove(os.path.join(upload_folder, file_name_))

    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    # 这里需要添加文件处理逻辑
    main_process.main_process()
    # 清空json文件夹
    if os.path.exists(json_folder):
        for file_name in os.listdir(json_folder):
            os.remove(os.path.join(json_folder, file_name))
    target_to_json.process_target_to_json()
    
   
    # 获取json_folder文件夹里所有文件的内容
    json_files = glob.glob(os.path.join(json_folder, "*.json"))
    # 将json文件解析为json，并以json返回
    json_data = []
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            json_data.append(json.load(f))
    # TODO:保存excel文件和json文件
    # 读取二进制流，保证只有一个excel文件
    excel_files = glob.glob(os.path.join(excel_folder, "*.xlsx"))
    if len(excel_files) != 1:
        raise HTTPException(status_code=400, detail="Excel file not found")
    excel_file = excel_files[0]
    # 读取excel文件，并用 BytesIO 包装一下
    excel_file_content = BytesIO(excel_file)
    # 将excel_file_content 保存到数据库中

    # 将json_data 保存到数据库中
    json_data_content = BytesIO(json_data)
    # 将json_data_content 保存到数据库中
    


    return json_data[0]

    # all_files_content = {}
    # for json_file in json_files:
    #     with open(json_file, "r", encoding="utf-8") as f:
    #         file_content = f.read()
    #         all_files_content[os.path.basename(json_file)] = file_content
    