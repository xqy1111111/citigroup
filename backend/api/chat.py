
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from models.chat import ChatHistory, Message
from models.user import User

from services.ai_service import AIService
from services.DataStructuring.DataStructuring import main_process
from services import target_to_json
import shutil
import os
import platform
import glob


router = APIRouter()


ai_service = AIService()

@router.post("", response_model=Message)
async def chat(message: str):
    """
    处理用户的聊天请求
    """
    response_text = await ai_service.chat(message)
    return Message(sayer="assistant", text=response_text)

@router.post("/with-file", response_model=Message)
async def chat_with_file(message: str, file: UploadFile = File(...)):
    """
    处理带文件的聊天请求
    """
    # 保存上传的文件到指定文件夹
    if platform.system() == "Windows":
        upload_folder = "backend\\services\\DataStructuring\\DataStructuring\\SourceData"
    else:
        upload_folder = "backend/services/DataStructuring/DataStructuring/SourceData"
    
    file_path = os.path.join(upload_folder, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 这里需要添加文件处理逻辑
    await main_process()
    await target_to_json()
    if platform.system() == "Windows":
        json_folder = "backend\\services\\DataStructuring\\DataStructuring\\JsonData"
    else:
        json_folder = "backend/services/DataStructuring/DataStructuring/JsonData"
    
   
    # 获取json_folder文件夹里所有文件的内容
    json_files = glob.glob(os.path.join(json_folder, "*.json"))
    all_files_content = ""
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            all_files_content += f.read() + "\n"

    message = message + " " + all_files_content
    response_text = await ai_service.chat(message)
    return Message(sayer="assistant", text=response_text)

# @router.get("/history/{user_id}", response_model=List[ChatHistory])
# async def get_chat_history_list(user_id: str):
#     """获取用户的聊天历史列表"""
#     pass

# @router.get("/history/{user_id}/{history_id}/messages", response_model=List[Message])
# async def get_chat_messages(user_id: str, history_id: str):
#     """获取特定聊天历史的消息列表"""
#     pass

# @router.delete("/history/{user_id}/{history_id}")
# async def delete_chat_history(user_id: str, history_id: str):
#     """删除特定的聊天历史"""
#     pass 

