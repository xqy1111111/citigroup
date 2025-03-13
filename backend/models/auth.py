"""
认证相关的数据模型
定义用于身份验证和授权的Pydantic模型
"""
from pydantic import BaseModel, Field, EmailStr, validator, constr
from typing import Optional
from datetime import datetime
import re

class Token(BaseModel):
    """
    令牌响应模型
    
    详细说明:
    - 此模型用于API返回JWT访问令牌
    - 包含令牌本身和令牌类型
    - 符合OAuth2的Bearer Token规范
    """
    access_token: str  # JWT访问令牌
    token_type: str = "bearer"  # OAuth2标准使用bearer令牌类型

class TokenData(BaseModel):
    """
    令牌数据模型
    
    详细说明:
    - 此模型用于存储从JWT令牌中解析出的数据
    - 包含用户ID和权限范围
    - 用于内部处理，不直接暴露给API
    """
    user_id: Optional[str] = None  # 用户ID
    scopes: list[str] = []  # 用户权限范围，用于基于角色的访问控制

class TokenPayload(BaseModel):
    """
    JWT令牌负载模型
    
    详细说明:
    - 此模型定义JWT令牌中实际存储的数据结构
    - 包含标准的JWT字段如subject(sub)、过期时间(exp)和签发时间(iat)
    - 以及自定义的权限范围(scopes)
    """
    sub: Optional[str] = None  # subject，通常是用户ID
    exp: Optional[datetime] = None  # 过期时间
    iat: Optional[datetime] = None  # 签发时间
    scopes: list[str] = []  # 权限范围

class UserLogin(BaseModel):
    """
    用户登录请求模型
    
    详细说明:
    - 此模型用于处理用户登录请求
    - 支持使用用户名或电子邮件进行登录
    - 包含基本的密码长度验证
    """
    username_or_email: str = Field(
        ..., 
        description="用户名或电子邮件",
        example="user123或user@example.com"
    )
    password: str = Field(
        ..., 
        min_length=6, 
        description="用户密码，至少6个字符",
        example="securepassword123"
    )

class UserRegister(BaseModel):
    """
    用户注册请求模型
    
    详细说明:
    - 此模型用于处理新用户注册请求
    - 包含完整的用户信息验证
    - 验证用户名格式、密码强度、邮箱格式等
    """
    # 用户名：3-50个字符，只允许字母、数字、下划线
    username: constr(min_length=3, max_length=50) = Field(
        ..., 
        description="用户名，3-50个字符，只允许字母、数字和下划线",
        example="user123"
    )
    
    # 电子邮件：使用EmailStr类型自动验证格式
    email: EmailStr = Field(
        ..., 
        description="有效的电子邮件地址",
        example="user@example.com"
    )
    
    # 密码：至少8个字符
    password: str = Field(
        ..., 
        min_length=8, 
        description="用户密码，至少8个字符，建议包含字母、数字和特殊字符",
        example="securepassword123"
    )
    
    # 确认密码
    password_confirm: str = Field(
        ..., 
        description="确认密码，必须与密码字段匹配",
        example="securepassword123"
    )
    
    # 可选的头像URL
    profile_picture: Optional[str] = Field(
        None, 
        description="用户头像URL(可选)",
        example="https://example.com/avatar.jpg"
    )
    
    # 用户名格式验证
    @validator('username')
    def username_alphanumeric(cls, v):
        """
        验证用户名只包含字母、数字和下划线
        """
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    # 密码强度验证
    @validator('password')
    def password_strength(cls, v):
        """
        验证密码强度，要求包含至少一个字母和一个数字
        """
        if not re.search(r'[A-Za-z]', v) or not re.search(r'[0-9]', v):
            raise ValueError('密码必须包含至少一个字母和一个数字')
        return v
    
    # 确认密码验证
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        """
        验证确认密码与密码是否匹配
        """
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不匹配')
        return v
    
    class Config:
        """
        模型配置
        """
        # 示例数据，用于API文档
        # 在Pydantic V2中，使用json_schema_extra而不是schema_extra
        json_schema_extra = {
            "example": {
                "username": "user123",
                "email": "user@example.com",
                "password": "securepassword123",
                "password_confirm": "securepassword123",
                "profile_picture": "https://example.com/avatar.jpg"
            }
        } 