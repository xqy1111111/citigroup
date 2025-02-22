from fastapi import APIRouter, HTTPException, Depends
from db.db_util import create_user, authenticate_user, get_user_by_id
from models.user import UserCreate, UserResponse, UserAuth, AuthResponse

router = APIRouter()

# 用户创建路由
@router.post("/", response_model=UserResponse)
async def create_new_user(user: UserCreate):
    """
    创建一个新的用户
    :param user:UserCreate
    :return: user id
    """
    user_id = create_user(user.username, user.email, user.password, user.profile_picture)
    return user_id

# 用户认证路由
@router.post("/authenticate/", response_model=AuthResponse)
async def authenticate_user_request(user: UserAuth):
    """
    认证用户的登陆
    :param user:UserAuth
    :return: 如果成功，则返回AuthResponse，包含用户的user_id
             否则返回status_code:401
    """
    user_id = authenticate_user(user.username_or_email, user.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(user_id=user_id)

# 获取用户信息路由
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    通过user_id获得用户的信息
    :param user_id: 就是user的 _id
    :return: 如果成功，则返回user:UserResponse
             否则返回status_code:404
    """
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
