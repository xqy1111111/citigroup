from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from bson import ObjectId

class MessageBase(BaseModel):
    sayer: str  # "user" 或 "assistant"
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)

class Message(MessageBase):
    pass

class ChatHistoryBase(BaseModel):
    user_id: str

class ChatHistoryCreate(ChatHistoryBase):
    pass

class ChatHistoryInDB(ChatHistoryBase):
    chat_history_id: str = Field(default_factory=lambda: str(ObjectId()))
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ChatHistory(ChatHistoryBase):
    chat_history_id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 