"""
认证系统数据模型模块

此模块定义了与用户认证、授权相关的所有Pydantic数据模型，包括：
1. 令牌模型 - 用于JWT令牌的创建、验证和处理
2. 用户认证模型 - 用于登录和注册请求的数据验证
3. 验证器 - 确保用户提供的信息符合安全标准

这些模型通过Pydantic提供的类型系统和验证器，确保API收到的数据符合预期格式，
提高了系统的安全性和可靠性，同时为API文档生成提供了基础。
"""
from pydantic import BaseModel, Field, EmailStr, validator, constr
from typing import Optional
from datetime import datetime
import re

class Token(BaseModel):
    """
    令牌响应模型
    
    详细说明:
    此模型定义了认证成功后返回给客户端的JWT令牌结构。
    遵循OAuth2的Bearer令牌规范，包含访问令牌和令牌类型。
    前端应将此令牌保存并在后续请求的Authorization头中使用。
    
    字段说明:
    - access_token: JWT格式的访问令牌字符串
    - token_type: 令牌类型，固定为"bearer"（OAuth2标准）
    
    使用示例:
    ```
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
    }
    ```
    """
    access_token: str  # JWT访问令牌
    token_type: str = "bearer"  # OAuth2标准使用bearer令牌类型

class TokenData(BaseModel):
    """
    令牌数据模型
    
    详细说明:
    此模型用于内部处理JWT令牌中解析出的数据。
    它从令牌载荷中提取用户标识和权限信息，供系统进行身份验证和授权判断。
    不直接暴露给API客户端，仅在服务器内部使用。
    
    字段说明:
    - user_id: 令牌关联的用户唯一标识符
    - scopes: 用户权限列表，用于实现基于角色的访问控制(RBAC)
    
    用途:
    - 在安全依赖项中验证用户身份
    - 检查用户是否有权访问特定资源
    - 跟踪API调用的用户来源
    """
    user_id: Optional[str] = None  # 用户ID
    scopes: list[str] = []  # 用户权限范围，用于基于角色的访问控制

class TokenPayload(BaseModel):
    """
    JWT令牌负载模型
    
    详细说明:
    此模型定义了JWT令牌内部的负载(payload)结构。
    包含JWT规范的标准字段和系统自定义字段，用于令牌的创建和解析。
    结构符合RFC 7519 JWT规范，确保与标准JWT库兼容。
    
    字段说明:
    - sub: (subject)令牌主体，通常是用户ID
    - exp: (expiration time)令牌过期时间
    - iat: (issued at)令牌创建时间
    - scopes: 用户权限列表，非标准JWT字段，用于自定义授权逻辑
    
    安全考量:
    - exp字段确保令牌有限期，减少泄露风险
    - iat字段可用于实现令牌轮换策略
    - 敏感信息不应存储在JWT中，因为载荷可被解码(虽然无法伪造)
    """
    sub: Optional[str] = None  # subject，通常是用户ID
    exp: Optional[datetime] = None  # 过期时间
    iat: Optional[datetime] = None  # 签发时间
    scopes: list[str] = []  # 权限范围

class UserLogin(BaseModel):
    """
    用户登录请求模型
    
    详细说明:
    此模型用于验证用户登录请求中提供的凭据。
    支持使用用户名或电子邮件作为标识符，增加登录的灵活性。
    设置了基本的密码长度验证，确保安全性。
    
    字段说明:
    - username_or_email: 用户名或电子邮件地址，作为用户唯一标识符
    - password: 用户密码，设置了最小长度要求
    
    验证规则:
    - 密码长度至少6个字符
    
    API使用示例:
    ```json
    {
        "username_or_email": "user123",
        "password": "my-secure-password"
    }
    ```
    或
    ```json
    {
        "username_or_email": "user@example.com",
        "password": "my-secure-password"
    }
    ```
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
    此模型定义了新用户注册时需要提供的信息和验证规则。
    实现了全面的数据验证，确保用户提供的信息符合系统要求。
    包含字段验证和自定义验证器，强制实施密码策略和用户名规则。
    
    字段说明:
    - username: 用户唯一标识符，3-50个字符，仅允许字母、数字和下划线
    - email: 有效的电子邮件地址，用于账户验证和通信
    - password: 用户密码，至少8个字符，必须包含字母和数字
    - password_confirm: 确认密码，必须与密码字段匹配
    - profile_picture: 可选的用户头像URL
    
    验证规则:
    - 用户名只能包含字母、数字和下划线
    - 密码必须包含至少一个字母和一个数字
    - 两次输入的密码必须匹配
    
    API使用示例:
    ```json
    {
        "username": "newuser123",
        "email": "newuser@example.com",
        "password": "SecurePass123",
        "password_confirm": "SecurePass123",
        "profile_picture": "https://example.com/avatar.jpg"
    }
    ```
    """
    # 用户名：3-50个字符，只允许字母、数字、下划线
    username: str = Field(
        ..., 
        description="用户名，3-50个字符，只允许字母、数字和下划线",
        example="user123",
        json_schema_extra={"pattern": "^[a-zA-Z0-9_]+$", "min_length": 3, "max_length": 50}
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
        验证用户名格式
        
        详细说明:
        确保用户名只包含允许的字符（字母、数字和下划线）。
        这种限制可防止用户名中包含可能导致安全问题的特殊字符，
        如SQL注入或XSS攻击字符。
        
        参数:
            v: 要验证的用户名字符串
            
        返回:
            验证通过的用户名
            
        异常:
            ValueError: 如果用户名包含非法字符
        """
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    # 密码强度验证
    @validator('password')
    def password_strength(cls, v):
        """
        验证密码强度
        
        详细说明:
        实施基本的密码强度策略，要求密码至少包含一个字母和一个数字。
        这大大提高了密码的复杂性，使其更难被暴力破解。
        实际应用中可能还需要额外的验证，如特殊字符要求、大小写混合等。
        
        参数:
            v: 要验证的密码字符串
            
        返回:
            验证通过的密码
            
        异常:
            ValueError: 如果密码不符合强度要求
        """
        if not re.search(r'[A-Za-z]', v) or not re.search(r'[0-9]', v):
            raise ValueError('密码必须包含至少一个字母和一个数字')
        return v
    
    # 确认密码验证
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        """
        验证两次输入的密码是否匹配
        
        详细说明:
        确保用户正确输入了密码，防止因输入错误导致无法登录。
        此验证器依赖于前面的password字段，如果password字段验证失败，
        此验证器不会被调用。
        
        参数:
            v: 确认密码字段值
            values: 当前已验证字段的值，包含password字段
            
        返回:
            验证通过的确认密码
            
        异常:
            ValueError: 如果两次输入的密码不匹配
        """
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不匹配')
        return v
    
    class Config:
        """
        Pydantic模型配置
        
        详细说明:
        为模型定义全局配置，如示例数据、额外属性行为等。
        这些配置不仅用于内部验证逻辑，还影响API文档的生成方式。
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