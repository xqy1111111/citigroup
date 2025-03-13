"""
认证相关的数据模型
定义用于身份验证和授权的Pydantic模型
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    """
    令牌响应模型
    
    用于返回JWT访问令牌和令牌类型
    """
    access_token: str
    token_type: str = "bearer"  # OAuth2标准使用bearer令牌类型

class TokenData(BaseModel):
    """
    令牌数据模型
    
    用于存储令牌中包含的数据
    """
    user_id: Optional[str] = None
    scopes: list[str] = []  # 用户权限范围，用于基于角色的访问控制

class TokenPayload(BaseModel):
    """
    JWT令牌负载模型
    
    定义JWT令牌中存储的字段
    """
    sub: Optional[str] = None  # subject，通常是用户ID
    exp: Optional[datetime] = None  # 过期时间
    iat: Optional[datetime] = None  # 签发时间
    scopes: list[str] = []  # 权限范围

class UserLogin(BaseModel):
    """
    用户登录请求模型
    
    用于处理用户登录请求
    """
    username_or_email: str = Field(..., description="用户名或电子邮件")
    password: str = Field(..., min_length=6, description="用户密码，至少6个字符")

class UserRegister(BaseModel):
    """
    用户注册请求模型
    
    用于处理用户注册请求
    """
    username: str = Field(..., min_length=3, max_length=50, description="用户名，3-50个字符")
    email: EmailStr = Field(..., description="有效的电子邮件地址")
    password: str = Field(..., min_length=8, description="用户密码，至少8个字符")
    password_confirm: str = Field(..., description="确认密码，必须与密码字段匹配")
    profile_picture: Optional[str] = Field(None, description="用户头像URL")
    
    class Config:
        """
        模型配置
        """
        # 示例数据，用于API文档
        schema_extra = {
            "example": {
                "username": "user123",
                "email": "user@example.com",
                "password": "securepassword",
                "password_confirm": "securepassword",
                "profile_picture": "https://example.com/avatar.jpg"
            }
        } 