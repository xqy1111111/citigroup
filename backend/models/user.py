from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    
class UserCreate(UserBase):
    password: str
    
class UserInDB(UserBase):
    user_id: str = Field(default_factory=lambda: str(ObjectId()))
    password_hash: str
    repo_ids: List[str] = []
    chat_history_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    
class User(UserBase):
    user_id: str
    repo_ids: List[str]
    chat_history_ids: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True 