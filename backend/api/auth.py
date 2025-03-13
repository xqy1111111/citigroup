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
    
    注册新用户并返回访问令牌
    
    参数:
        user_data: 包含用户注册信息的模型
        
    返回:
        Token: 包含访问令牌的响应
        
    异常:
        HTTPException 400: 如果密码不匹配或用户名/邮箱已存在
    """
    # 验证两次密码输入是否匹配
    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码不匹配"
        )
    
    # 检查用户名是否已存在
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 对密码进行哈希处理
    hashed_password = get_password_hash(user_data.password)
    
    # 创建新用户
    user_id = create_user(
        user_data.username, 
        user_data.email, 
        hashed_password,  # 传入哈希后的密码而不是明文密码
        user_data.profile_picture
    )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=access_token_expires
    )
    
    # 返回令牌
    return Token(access_token=access_token)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录获取访问令牌
    
    使用OAuth2密码流程进行身份验证并返回访问令牌
    
    参数:
        form_data: OAuth2表单数据，包含username和password字段
        
    返回:
        Token: 包含访问令牌的响应
        
    异常:
        HTTPException 401: 如果凭据无效
    """
    # 尝试通过用户名找到用户
    user = get_user_by_username(form_data.username)
    
    # 如果找不到用户，尝试通过邮箱找到用户
    if not user:
        user = get_user_by_email(form_data.username)
    
    # 如果仍找不到用户或密码不匹配，则返回凭据无效错误
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    # 返回令牌
    return Token(access_token=access_token)

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """
    用户登录
    
    使用用户名/邮箱和密码进行身份验证并返回访问令牌
    
    参数:
        user_data: 包含登录信息的模型
        
    返回:
        Token: 包含访问令牌的响应
        
    异常:
        HTTPException 401: 如果凭据无效
    """
    # 尝试通过用户名找到用户
    user = get_user_by_username(user_data.username_or_email)
    
    # 如果找不到用户，尝试通过邮箱找到用户
    if not user:
        user = get_user_by_email(user_data.username_or_email)
    
    # 如果仍找不到用户或密码不匹配，则返回凭据无效错误
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    # 返回令牌
    return Token(access_token=access_token)

@router.get("/me", response_model=dict)
async def read_users_me(current_user = Depends(get_current_user)):
    """
    获取当前用户信息
    
    返回当前经过身份验证的用户的信息
    
    参数:
        current_user: 当前用户，从令牌中获取
        
    返回:
        dict: 包含用户信息的字典
    """
    # 在实际应用中，应返回完整的用户信息
    # 这里简单返回用户ID以演示身份验证流程
    return {"user_id": current_user} 