from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from ...models.chat import ChatHistory, Message

from ...services.ai_service import AIService

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]  # 所有聊天操作都需要认证
)

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
    TODO: 实现文件处理逻辑
    """
    # 这里需要添加文件处理逻辑
    # modified_file = await PROCESS
    # message = message + " " + modified_file
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

