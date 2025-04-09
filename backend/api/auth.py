"""
认证API路由模块

此模块实现了用户身份验证系统的所有API端点，包括：
1. 用户注册 - 创建新用户账户并返回JWT令牌
2. 用户登录 - 验证凭据并签发访问令牌
3. 令牌管理 - 处理JWT令牌的签发和验证
4. 用户信息获取 - 通过token获取当前已认证用户的信息

这些API组成了完整的身份验证系统，支持系统的用户注册、登录功能和安全访问控制。
安全性设计基于JWT(JSON Web Token)，确保服务器无状态的同时提供可靠的身份验证。
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from core.security import (
    create_access_token, 
    get_password_hash, 
    verify_password, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user
)
from models.auth import Token, UserLogin, UserRegister
from db.db_util import create_user, get_user_by_username, get_user_by_email

router = APIRouter()

@router.post("/register", response_model=Token)
async def register_user(user_data: UserRegister):
    """
    用户注册API
    
    详细说明:
    此端点处理新用户注册流程，包括输入验证、用户创建和令牌签发。
    一旦注册成功，用户将获得JWT访问令牌，可立即使用系统功能。
    
    实现流程:
    1. 验证两次输入的密码是否一致
    2. 检查用户名和邮箱是否已被使用（唯一性检查）
    3. 对密码进行安全哈希处理
    4. 创建新用户并生成访问令牌
    
    安全特性:
    - 密码在存储前使用bcrypt算法进行哈希处理
    - 用户名和邮箱的唯一性验证防止重复注册
    - 生成的JWT令牌有时效限制，增强安全性
    
    参数:
        user_data: 包含用户注册信息的模型(用户名、邮箱、密码等)
        
    返回:
        Token: 包含访问令牌的响应，用于后续的认证
        
    异常:
        HTTPException 400: 如果密码不匹配或用户名/邮箱已存在
    """
    # 1. 验证两次密码输入是否匹配
    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码不匹配，请确保两次输入的密码一致"
        )
    
    # 2. 检查用户名是否已存在 - 用户名唯一性检查
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用，请选择其他用户名"
        )
    
    # 3. 检查邮箱是否已存在 - 邮箱唯一性检查
    existing_email = get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此邮箱已被注册，请使用其他邮箱或找回密码"
        )
    
    # 4. 对密码进行哈希处理，增强安全性
    # 使用bcrypt算法，确保即使数据库泄露，密码也不会被轻易破解
    hashed_password = get_password_hash(user_data.password)
    
    # 5. 创建新用户，传入哈希后的密码
    user_id = create_user(
        user_data.username, 
        user_data.email, 
        hashed_password,  # 传入哈希后的密码而不是明文密码
        user_data.profile_picture
    )
    
    # 6. 创建访问令牌 (JWT)，设置过期时间
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id)},  # sub(subject)字段用于存储用户ID
        expires_delta=access_token_expires
    )
    
    # 7. 返回JWT令牌
    return Token(access_token=access_token)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2标准登录API
    
    详细说明:
    此端点实现OAuth2密码授权流程，用于前端登录表单提交。
    遵循OAuth2标准，通过form表单提交用户名和密码，返回JWT访问令牌。
    
    OAuth2流程:
    1. 客户端提交用户名和密码
    2. 服务器验证凭据并签发访问令牌
    3. 客户端使用令牌访问受保护资源
    
    参数:
        form_data: OAuth2表单数据，自动由FastAPI提取，包含username和password字段
        
    返回:
        Token: 包含访问令牌的响应，用于后续认证
        
    异常:
        HTTPException 401: 如果用户名/密码不正确
    """
    # 1. 尝试通过用户名找到用户
    user = get_user_by_username(form_data.username)
    
    # 2. 如果找不到用户，尝试通过邮箱找到用户(支持邮箱登录)
    if not user:
        user = get_user_by_email(form_data.username)
    
    # 3. 如果仍找不到用户或密码不匹配，则返回认证失败
    # 注意这里使用password_hash而不是password字段，因为数据库中存储的是哈希密码
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},  # OAuth2规范的WWW-Authenticate头
        )
    
    # 4. 验证成功，创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    # 5. 返回访问令牌
    return Token(access_token=access_token)

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """
    自定义登录API
    
    详细说明:
    此端点提供比标准OAuth2更灵活的登录方式，支持通过用户名或邮箱登录。
    接收JSON格式的登录请求，适合现代前端应用使用。
    
    灵活性特点:
    1. 支持用户名或邮箱登录（单个字段兼容两种方式）
    2. 使用JSON请求体而非表单，更符合RESTful API设计
    3. 更易于集成到各种前端框架
    
    参数:
        user_data: 包含登录信息的模型，有username_or_email和password字段
        
    返回:
        Token: 包含访问令牌的响应
        
    异常:
        HTTPException 401: 如果认证失败
    """
    # 1. 尝试通过用户名找到用户
    user = get_user_by_username(user_data.username_or_email)
    
    # 2. 如果找不到用户，尝试通过邮箱找到用户
    if not user:
        user = get_user_by_email(user_data.username_or_email)
    
    # 3. 如果仍找不到用户或密码不匹配，则返回认证失败
    # 注意使用password_hash字段进行验证
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. 验证成功，创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    # 5. 返回访问令牌
    return Token(access_token=access_token)

@router.get("/me", response_model=dict)
async def read_users_me(current_user = Depends(get_current_user)):
    """
    获取当前用户信息API
    
    详细说明:
    此端点用于验证当前用户的认证状态并返回其信息。
    它使用JWT令牌认证，从Authorization头中提取令牌并验证。
    这是典型的受保护资源，用于测试认证系统是否正常工作。
    
    认证流程:
    1. FastAPI从请求中提取授权头中的JWT令牌
    2. get_current_user依赖项验证令牌的有效性
    3. 从令牌中提取用户ID并返回
    
    参数:
        current_user: 当前用户ID，由get_current_user依赖项自动提取和验证
        
    返回:
        dict: 包含用户信息的字典，当前实现简单返回用户ID
        
    安全性:
    - 如果令牌无效或过期，get_current_user依赖项会抛出401异常
    - 此端点仅对已认证用户可用
    """
    # 返回用户信息
    # 在完整实现中，应该从数据库获取用户详细信息后返回
    # 目前简单返回用户ID，以演示认证流程
    return {"user_id": current_user} 