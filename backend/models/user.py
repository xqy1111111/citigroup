"""
用户数据模型模块

这个模块定义了与用户相关的所有数据模型，用于:
1. 验证API请求中的用户数据
2. 构建API响应中的用户信息
3. 在数据库操作中表示用户文档结构

在Web应用中，用户模型通常是最核心的数据结构之一，
因为几乎所有功能都会涉及到用户身份和权限。
"""
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

# 用户创建模型，用于创建新用户时的输入数据验证
class UserCreate(BaseModel):
    """
    用户创建模型
    
    用于新用户注册API的请求体验证。
    确保客户端提供了创建用户所需的所有必要信息，
    并且这些信息符合预期的格式。
    """
    username: str = Field(..., description="用户名，用于登录和标识用户", min_length=3, max_length=50)
    email: EmailStr = Field(..., description="用户的电子邮件地址，用于通知和账号恢复")
    password: str = Field(..., description="用户密码，将在存储前进行哈希处理", min_length=8)
    profile_picture: Optional[str] = Field(None, description="用户头像的URL或路径，可选字段")

    class Config:
        """
        模型配置
        
        配置Pydantic模型的行为，如字符串处理规则等。
        """
        str_min_length = 1  # 所有字符串字段的最小长度，防止空字符串
        str_strip_whitespace = True  # 自动去除字符串字段的前后空格，改善用户体验
        
        # 添加示例，方便API文档和测试
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "password": "securepassword123",
                "profile_picture": "https://example.com/avatars/johndoe.jpg"
            }
        }

# 用户响应模型，用于返回用户信息
class UserResponse(BaseModel):
    """
    用户响应模型
    
    用于API返回用户信息时的数据结构。
    不包含敏感信息(如密码)，只包含可以安全返回给客户端的字段。
    
    这个模型用于:
    1. 用户个人资料API
    2. 用户列表API
    3. 其他需要返回用户信息的场景
    """
    id: str = Field(..., description="用户在数据库中的唯一标识符")
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="用户电子邮件")
    profile_picture: Optional[str] = Field(None, description="用户头像URL")
    repos: List[str] = []
    collaborations: List[str] = []

    class Config:
        """
        模型配置
        """
        from_attributes = True  # 允许从ORM模型(如SQLAlchemy)或其他对象创建Pydantic模型
        
        # 设置示例数据
        schema_extra = {
            "example": {
                "id": "60d21b4967d0d8992e610c85",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "profile_picture": "https://example.com/avatars/johndoe.jpg",
                "repos": ["60d21b4967d0d8992e610c86", "60d21b4967d0d8992e610c87"],
                "collaborations": ["60d21b4967d0d8992e610c88"]
            }
        }

# 用户认证请求模型，用于用户登录时的请求数据
class UserAuth(BaseModel):
    """
    用户认证请求模型
    
    用于登录API的请求体验证。
    支持使用用户名或电子邮件进行登录，增加灵活性。
    
    登录流程:
    1. 客户端提交用户名/邮箱和密码
    2. 服务器验证凭据
    3. 验证成功后返回访问令牌(JWT)
    """
    username_or_email: str = Field(..., description="用户登录名，可以是用户名或电子邮件地址")
    password: str = Field(..., description="用户密码")
    
    class Config:
        """模型配置"""
        schema_extra = {
            "example": {
                "username_or_email": "johndoe或john.doe@example.com",
                "password": "securepassword123"
            }
        }

# 用户认证响应模型
class AuthResponse(BaseModel):
    """
    认证响应模型
    
    用于登录或其他认证API的响应。
    通常包含用户ID和成功消息，有时也包含访问令牌。
    
    注意: 在实际项目中，通常会返回JWT令牌而非用户ID，
    参见auth.py中的Token模型。
    """
    user_id: str = Field(..., description="已认证用户的数据库ID")
    message: str = Field("Authentication successful", description="认证结果消息")
    
    class Config:
        """模型配置"""
        schema_extra = {
            "example": {
                "user_id": "60d21b4967d0d8992e610c85",
                "message": "Authentication successful"
            }
        }
