from typing import Optional
from datetime import timedelta
from ..models.user import UserCreate, UserInDB, User
from ..core.security import get_password_hash, verify_password, create_access_token
from ..db.repositories.user import UserRepository
from fastapi import HTTPException

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def create_user(self, user_data: UserCreate) -> User:
        # 检查用户名是否已存在
        existing_user = await self.user_repository.find_by_username(user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # 创建新用户
        user_in_db = UserInDB(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password)
        )
        
        # 保存到数据库
        user_id = await self.user_repository.create(user_in_db)
        return await self.user_repository.get(user_id)

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        # 查找用户
        user = await self.user_repository.find_by_username(username)
        if not user:
            return None
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return None
            
        return user

    def create_user_token(self, user_id: str) -> dict:
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": access_token, "token_type": "bearer"} 