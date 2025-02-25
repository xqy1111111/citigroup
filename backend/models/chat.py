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


class text(BaseModel):
    question: Message
    answer: Message
class ChatHistory(BaseModel):
    user_id:str
    repo_id:str
    texts: List[text] = []
    _id:str
    class Config:
        arbitrary_types_allowed = True


    
