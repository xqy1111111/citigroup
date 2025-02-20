from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from ...models.chat import ChatHistory, Message
from ...models.user import User
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]  # 所有聊天操作都需要认证
)

#TODO: 用户跟AI的聊天，可能上传文件来chat, 内部调用 structure_file 的 api
@router.post("", response_model=Message)
async def chat(message: str):
    """发送聊天消息"""
    pass


@router.post("/with-file")
async def chat_with_file(message: str, file: UploadFile = File(...)):
    """带文件的聊天消息"""
    pass



# @router.get("/history/{user_id}", response_model=List[ChatHistory])
# async def get_chat_history_list(user_id: str):
#     """获取用户的聊天历史列表"""
#     pass

# @router.get("/history/{user_id}/{history_id}/messages", response_model=List[Message])
# async def get_chat_messages(user_id: str, history_id: str):
#     """获取特定聊天历史的消息"""
#     pass

# @router.delete("/history/{user_id}/{history_id}")
# async def delete_chat_history(user_id: str, history_id: str):
#     """删除聊天历史"""
#     pass 

