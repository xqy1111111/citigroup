from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .base import BaseRepository
from ...models.user import UserInDB, User

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")

    async def create_user(self, user: UserInDB) -> str:
        """创建新用户"""
        user_dict = user.model_dump()
        return await self.insert_one(user_dict)

    async def find_by_username(self, username: str) -> Optional[UserInDB]:
        """根据用户名查找用户"""
        user_dict = await self.find_one({"username": username})
        return UserInDB(**user_dict) if user_dict else None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        user_dict = await self.find_one({"_id": self._convert_id(user_id)})
        return User(**user_dict) if user_dict else None

    async def update_user_repos(self, user_id: str, repo_ids: List[str]) -> bool:
        """更新用户的仓库列表"""
        return await self.update_one(
            {"_id": self._convert_id(user_id)},
            {"repo_ids": repo_ids, "updated_at": datetime.now()}
        ) 