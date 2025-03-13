"""
认证路由模块
处理用户注册、登录和令牌刷新等身份验证相关操作
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
    用户注册
    
    详细说明:
    1. 验证两次输入的密码是否一致
    2. 检查用户名和邮箱是否已被使用（唯一性检查）
    3. 对密码进行安全哈希处理
    4. 创建新用户并生成访问令牌
    
    流程:
    - 接收用户提交的注册信息
    - 进行各种验证（密码匹配、用户名和邮箱唯一性）
    - 如果验证通过，创建用户并返回访问令牌
    - 如果验证失败，返回相应的错误信息
    
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
    用户登录获取访问令牌
    
    详细说明:
    1. 此API端点处理标准OAuth2密码流程的登录请求
    2. 验证用户提供的用户名和密码
    3. 如果验证成功，生成并返回JWT访问令牌
    
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
    用户登录
    
    详细说明:
    1. 此API端点是自定义登录流程，接受用户名/邮箱和密码
    2. 比OAuth2更灵活，支持用户名或邮箱登录
    3. 验证成功后返回JWT访问令牌
    
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
    获取当前用户信息
    
    详细说明:
    1. 此API端点用于获取当前已认证用户的信息
    2. 使用JWT令牌进行认证，令牌通过请求头中的Authorization字段传递
    3. 依赖项automatically从令牌中提取用户ID
    
    参数:
        current_user: 当前用户ID，由get_current_user依赖项自动提取和验证
        
    返回:
        dict: 包含用户信息的字典
    """
    # 返回用户信息
    # 在完整实现中，应该从数据库获取用户详细信息后返回
    # 目前简单返回用户ID，以演示认证流程
    return {"user_id": current_user} 