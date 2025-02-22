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


from _file import download_file
router = APIRouter()


@router.post("/{file_id}/process", response_model=Message)
async def process_file_to_json(file_id: str):
    """
    处理带文件的聊天请求
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
    json_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "JsonData")
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
        shutil.copyfileobj(file_content, buffer)
    
    # 这里需要添加文件处理逻辑
    main_process.main_process()
    # 清空json文件夹
    if os.path.exists(json_folder):
        for file_name in os.listdir(json_folder):
            os.remove(os.path.join(json_folder, file_name))
    target_to_json.process_target_to_json()
    
   
    # 获取json_folder文件夹里所有文件的内容
    json_files = glob.glob(os.path.join(json_folder, "*.json"))
    all_files_content = {}
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            file_content = f.read()
            all_files_content[os.path.basename(json_file)] = file_content

    return all_files_content