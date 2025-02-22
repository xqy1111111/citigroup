from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    profile_picture: Optional[str] = None  # 可选字段

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    profile_picture: Optional[str] = None  # 可选字段
    repos: List[str] = []  # 用户的仓库ID列表
    collaborations: List[str] = []  # 用户的协作仓库ID列表

    class Config:
        orm_mode = True
