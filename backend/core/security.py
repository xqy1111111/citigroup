"""
安全核心模块
包含密码哈希和JWT令牌相关的功能
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# 创建密码上下文，用于哈希和验证密码
# 使用bcrypt算法，这是当前推荐的密码哈希算法之一
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 从环境变量获取密钥，如果不存在则使用默认值（生产环境中应始终设置安全的密钥）
# 在实际部署中，您应该使用强随机密钥并通过环境变量注入
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-should-be-in-env-var")
ALGORITHM = "HS256"  # 使用HS256算法，这是JWT中常用的算法
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 令牌有效期30分钟

# 创建OAuth2密码承载工具，用于从请求中提取令牌
# tokenUrl参数指定客户端获取令牌的URL端点
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配
    
    参数:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的哈希密码
        
    返回:
        bool: 如果密码匹配返回True，否则返回False
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    对明文密码进行哈希处理
    
    参数:
        password: 需要哈希的明文密码
        
    返回:
        str: 哈希后的密码，可以安全存储在数据库中
    """
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    参数:
        data: 要编码到令牌中的数据，通常包含用户ID
        expires_delta: 令牌的有效期，如果未提供则使用默认值
        
    返回:
        str: 编码后的JWT令牌
    """
    # 创建数据的副本，避免修改原始数据
    to_encode = data.copy()
    
    # 设置令牌过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 将过期时间添加到要编码的数据中
    to_encode.update({"exp": expire})
    
    # 使用密钥和算法对数据进行编码，创建JWT令牌
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    从令牌中获取当前用户
    
    参数:
        token: JWT令牌，由OAuth2PasswordBearer依赖项自动提取
        
    返回:
        用户对象: 当前经过身份验证的用户
        
    异常:
        HTTPException: 如果令牌无效或用户不存在，则引发401错误
    """
    # 创建凭据异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码令牌，提取数据
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 从令牌中提取用户ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # 创建令牌数据模型
        token_data = {"user_id": user_id}
    except JWTError:
        # 如果解码失败，则说明令牌无效
        raise credentials_exception
        
    # 这里需要从数据库获取用户
    # 实际实现时，应该调用db中的方法获取用户详情
    # 例如：user = get_user_by_id(token_data["user_id"])
    
    # 临时返回用户ID，实际实现应返回完整用户对象
    return token_data["user_id"]

async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    获取当前活跃用户，可用于验证用户是否已被禁用
    
    参数:
        current_user: 当前用户，从get_current_user依赖项获取
        
    返回:
        用户对象: 当前活跃用户
        
    异常:
        HTTPException: 如果用户被禁用，则引发400错误
    """
    # 在实际实现中，您可以检查用户是否被禁用
    # 例如：if current_user.disabled: raise HTTPException(...)
    
    return current_user 