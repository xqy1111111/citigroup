from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from ...models.user import UserCreate, User
from ...models.repo import Repo
from ...services.user_service import UserService
from ...db.repositories.user import UserRepository
from ...db.database import Database
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# 依赖注入
async def get_user_service():
    db = Database.get_db()
    user_repo = UserRepository(db)
    return UserService(user_repo)

@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """注册新用户"""
    try:
        user = await user_service.create_user(user_data)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login_user(
    username: str,
    password: str,
    user_service: UserService = Depends(get_user_service)
):
    """用户登录"""
    user = await user_service.authenticate(username, password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    return user_service.create_user_token(user.user_id)

@router.get("/{user_id}/repos", response_model=List[Repo])
async def get_user_repos(user_id: str):
    """获取用户的所有仓库"""
    pass

@router.get("/{user_id}/owned-repos", response_model=List[Repo])
async def get_owned_repos(user_id: str):
    """获取用户拥有的仓库"""
    pass

@router.get("/{user_id}/collaborated-repos", response_model=List[Repo])
async def get_collaborated_repos(user_id: str):
    """获取用户参与协作的仓库"""
    pass

@router.get("/{user_id}/me", response_model=User)
async def read_users_me(user_id: str):
    """获取当前用户信息"""
    pass 