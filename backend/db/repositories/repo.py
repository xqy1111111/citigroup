from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .base import BaseRepository
from ...models.repo import RepoInDB, Repo

class RepoRepository(BaseRepository):
    def __init__(self):
        super().__init__("repositories")

    async def create_repo(self, repo: RepoInDB) -> str:
        """创建新仓库"""
        repo_dict = repo.model_dump()
        return await self.insert_one(repo_dict)

    async def get_repo_by_id(self, repo_id: str) -> Optional[Repo]:
        """根据ID获取仓库"""
        repo_dict = await self.find_one({"_id": self._convert_id(repo_id)})
        return Repo(**repo_dict) if repo_dict else None

    async def get_user_owned_repos(self, user_id: str) -> List[Repo]:
        """获取用户拥有的仓库"""
        repos = await self.find_many({"owner_id": user_id})
        return [Repo(**repo) for repo in repos]

    async def get_user_collaborated_repos(self, user_id: str) -> List[Repo]:
        """获取用户参与协作的仓库"""
        repos = await self.find_many({"co_user_ids": user_id})
        return [Repo(**repo) for repo in repos]

    async def update_repo_files(self, repo_id: str, file_ids: List[str], structure_file_ids: List[str]) -> bool:
        """更新仓库的文件列表"""
        return await self.update_one(
            {"_id": self._convert_id(repo_id)},
            {
                "file_ids": file_ids,
                "structure_file_ids": structure_file_ids,
                "updated_at": datetime.now()
            }
        )

    async def update_collaborators(self, repo_id: str, co_user_ids: List[str]) -> bool:
        """更新仓库协作者"""
        return await self.update_one(
            {"_id": self._convert_id(repo_id)},
            {
                "co_user_ids": co_user_ids,
                "updated_at": datetime.now()
            }
        )

    async def delete_repo(self, repo_id: str) -> bool:
        """删除仓库"""
        return await self.delete_one({"_id": self._convert_id(repo_id)}) 