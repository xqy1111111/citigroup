"""
安全核心模块
包含密码哈希和JWT令牌相关的功能

详细说明:
这个模块实现了Web应用的两个核心安全功能：
1. 密码安全存储 - 使用bcrypt算法对密码进行单向哈希，而不是存储明文密码
2. JWT认证系统 - 创建和验证JSON Web Tokens，用于无状态认证

为什么需要这些功能？
- 密码哈希：即使数据库泄露，攻击者也无法获取用户的原始密码
- JWT认证：允许服务器在无需保存会话状态的情况下验证用户身份
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from jose import jwt, JWTError  # python-jose库用于处理JWT
from passlib.context import CryptContext  # passlib用于密码哈希
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer  # OAuth2密码流认证

# =============================== 密码哈希配置 ===============================

# 创建密码上下文，用于哈希和验证密码
# CryptContext是一个强大的密码哈希管理器，它处理密码的哈希和验证
# schemes=["bcrypt"] 表示使用bcrypt算法进行密码哈希
# bcrypt是一种专为密码设计的哈希算法，具有以下特点:
# 1. 自动加盐 - 每次哈希都自动加入随机盐值，防止彩虹表攻击
# 2. 计算缓慢 - 故意设计为计算密集型，防止暴力破解
# 3. 自适应 - 随着计算机性能提升可以调整工作因子
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =============================== JWT配置 ===============================

# 从环境变量获取密钥，如果不存在则使用默认值
# 注意：在生产环境中，应始终使用强随机生成的密钥并通过环境变量注入
# 不要在代码中硬编码密钥
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-should-be-in-env-var")

# 使用HS256算法，这是JWT中常用的算法
# HS256 = HMAC with SHA-256，基于密钥的签名算法
ALGORITHM = "HS256"  

# 令牌有效期30分钟
# 短期令牌增强安全性，即使令牌泄露，攻击者只能在有限时间内使用
ACCESS_TOKEN_EXPIRE_MINUTES = 30  

# =============================== OAuth2配置 ===============================

# 创建OAuth2密码认证方案
# OAuth2PasswordBearer是一个依赖项(Dependency)，会:
# 1. 从请求的Authorization头中提取Bearer令牌
# 2. 如果没有提供令牌或格式不正确，会自动返回401 Unauthorized响应
# tokenUrl参数指定客户端获取令牌的URL端点
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# =============================== 密码处理函数 ===============================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配
    
    详细说明:
    1. 此函数使用bcrypt算法验证用户输入的明文密码是否与数据库中存储的哈希密码匹配
    2. bcrypt会自动提取哈希中包含的盐值，然后使用相同的盐值对明文密码进行哈希处理
    3. 最后比较两个哈希值是否一致
    
    工作原理:
    - 用户登录时输入密码 -> plain_password
    - 数据库中存储的是之前经过bcrypt处理的密码哈希 -> hashed_password
    - verify函数对plain_password进行哈希处理(使用hashed_password中的盐)
    - 比较生成的哈希值与hashed_password是否一致
    
    :param plain_password: 用户输入的明文密码
    :param hashed_password: 数据库中存储的哈希密码
    :return: 如果密码匹配返回True，否则返回False
    """
    # verify方法会自动处理所有复杂的哈希比较逻辑
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    对明文密码进行哈希处理
    
    详细说明:
    1. 此函数使用bcrypt算法对用户密码进行单向哈希处理
    2. bcrypt会自动生成随机盐值并将其包含在最终的哈希字符串中
    3. 每次对同一个密码进行哈希，都会生成不同的哈希值(因为使用不同的盐)
    
    为什么需要哈希密码?
    - 即使数据库被攻破，攻击者也无法获取用户的原始密码
    - 哈希是单向操作，无法从哈希值反推出原始密码
    - 每个密码使用不同的盐值，防止通过预计算表(彩虹表)攻击
    
    :param password: 需要哈希的明文密码
    :return: 哈希后的密码字符串，可以安全存储在数据库中
    """
    # hash方法自动处理所有复杂的哈希生成逻辑，包括盐值生成
    return pwd_context.hash(password)

# =============================== JWT函数 ===============================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    详细说明:
    1. 此函数创建一个JWT(JSON Web Token)令牌，包含用户身份信息和过期时间
    2. JWT由三部分组成：头部(header)、载荷(payload)和签名(signature)
    3. 签名确保令牌未被篡改，只有拥有SECRET_KEY的服务器才能创建有效的签名
    
    JWT工作原理:
    - 服务器创建包含用户ID等信息的JWT令牌，并用密钥签名
    - 将JWT返回给客户端，客户端在后续请求中包含此令牌
    - 服务器验证JWT签名和有效期，无需查询数据库即可确认用户身份
    
    :param data: 要编码到令牌中的数据，通常包含用户ID ({"sub": "用户ID"})
    :param expires_delta: 令牌的有效期，如果未提供则使用默认值
    :return: 编码后的JWT令牌字符串
    """
    # 创建数据的副本，避免修改原始数据
    to_encode = data.copy()
    
    # 设置令牌过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 将过期时间添加到要编码的数据中
    # 标准JWT字段：exp(expiration time)表示令牌过期时间
    to_encode.update({"exp": expire})
    
    # 使用密钥和算法对数据进行编码，创建JWT令牌
    # 此步骤会生成包含头部、载荷和签名的完整JWT字符串
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# =============================== 依赖项函数 ===============================

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    从令牌中获取当前用户
    
    详细说明:
    1. 此函数是一个依赖项(FastAPI Dependency)，用于从请求中提取和验证JWT令牌
    2. 验证JWT令牌的签名是否有效，以及令牌是否已过期
    3. 从令牌中提取用户ID，用于识别当前用户
    
    工作原理:
    - FastAPI自动从请求的Authorization头中提取Bearer令牌
    - 此函数解码令牌并验证其完整性
    - 提取用户ID并返回，以便API端点知道是哪个用户在访问
    
    使用方式:
    ```
    @app.get("/users/me")
    async def read_users_me(current_user = Depends(get_current_user)):
        return {"user_id": current_user}
    ```
    
    :param token: JWT令牌，由OAuth2PasswordBearer依赖项自动从请求中提取
    :return: 用户ID，从令牌的sub字段中提取
    :raises HTTPException: 如果令牌无效或已过期，则引发401错误
    """
    # 创建凭据异常，用于令牌验证失败情况
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # 告诉客户端应使用Bearer令牌认证
    )
    
    try:
        # 解码令牌，验证签名和过期时间
        # 如果令牌被篡改或已过期，这一步会引发异常
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 从令牌中提取用户ID (stored in the "sub" claim)
        # "sub"(subject)是JWT的标准字段，通常用来存储用户ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # 创建令牌数据
        token_data = {"user_id": user_id}
    except JWTError:
        # 如果解码失败(令牌格式错误、签名无效或已过期)，则引发401错误
        raise credentials_exception
        
    # 在实际应用中，您可能需要从数据库中获取完整的用户信息
    # 例如: user = get_user_by_id(token_data["user_id"])
    # 如果用户不存在，则可以引发404错误
    
    # 临时返回用户ID
    # 实际实现中应返回完整用户对象
    return token_data["user_id"]

async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    获取当前活跃用户
    
    详细说明:
    1. 此函数是在get_current_user基础上的额外检查层
    2. 可用于验证用户是否已被禁用或处于非活跃状态
    3. 在需要确保用户处于活跃状态的API端点中使用
    
    使用方式:
    ```
    @app.get("/users/profile")
    async def read_profile(current_user = Depends(get_current_active_user)):
        return {"user": current_user}
    ```
    
    :param current_user: 当前用户ID，从get_current_user依赖项获取
    :return: 当前活跃用户ID
    :raises HTTPException: 如果用户被禁用，则引发400错误
    """
    # 在实际实现中，您可以检查用户是否被禁用
    # 例如：
    # user = get_user_by_id(current_user)
    # if user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user 