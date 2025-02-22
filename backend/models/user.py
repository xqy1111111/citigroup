from bson import ObjectId
from pydantic import BaseModel, EmailStr
from typing import Optional, List

# 用户创建模型，用于创建新用户时的输入数据验证
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    profile_picture: Optional[str] = None  # 可选字段，头像URL或路径

    class Config:
        str_min_length = 1  # 字符串字段最小长度为1
        str_strip_whitespace = True  # 去除字段的前后空格

# 用户响应模型，用于返回用户信息
class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    profile_picture: Optional[str] = None  # 可选字段
    repos: List[str] = []  # 用户拥有的仓库ID列表
    collaborations: List[str] = []  # 用户参与的仓库ID列表

    class Config:
        from_attributes = True  # 使得 Pydantic 能够将 MongoDB 返回的对象转化为模型对象

# 用户认证请求模型，用于用户登录时的请求数据
class UserAuth(BaseModel):
    username_or_email: str  # 用户名或邮箱
    password: str  # 明文密码

# 用户认证响应模型
class AuthResponse(BaseModel):
    user_id: str  # 用户的 MongoDB _id
    message: str = "Authentication successful"  # 默认的认证成功消息
