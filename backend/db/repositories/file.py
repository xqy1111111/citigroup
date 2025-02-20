from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .base import BaseRepository
from ...models.file import FileInDB, File, StructureFileInDB, StructureFile

class FileRepository(BaseRepository):
    def __init__(self):
        super().__init__("files")

    async def create_file(self, file: FileInDB) -> str:
        """创建新文件"""
        file_dict = file.model_dump()
        return await self.insert_one(file_dict)

    async def get_file_by_id(self, file_id: str) -> Optional[File]:
        """根据ID获取文件"""
        file_dict = await self.find_one({"_id": self._convert_id(file_id)})
        return File(**file_dict) if file_dict else None

    async def get_files_by_ids(self, file_ids: List[str]) -> List[File]:
        """根据ID列表获取多个文件"""
        files = await self.find_many({
            "_id": {"$in": [self._convert_id(fid) for fid in file_ids]}
        })
        return [File(**file) for file in files]

    async def update_file_content(self, file_id: str, content: str) -> bool:
        """更新文件内容"""
        return await self.update_one(
            {"_id": self._convert_id(file_id)},
            {
                "content": content,
                "updated_at": datetime.now()
            }
        )

    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        return await self.delete_one({"_id": self._convert_id(file_id)})

class StructureFileRepository(BaseRepository):
    def __init__(self):
        super().__init__("structure_files")

    async def create_structure_file(self, file: StructureFileInDB) -> str:
        """创建结构化文件"""
        file_dict = file.model_dump()
        return await self.insert_one(file_dict)

    async def get_structure_file_by_id(self, file_id: str) -> Optional[StructureFile]:
        """根据ID获取结构化文件"""
        file_dict = await self.find_one({"_id": self._convert_id(file_id)})
        return StructureFile(**file_dict) if file_dict else None

    async def get_structure_files_by_ids(self, file_ids: List[str]) -> List[StructureFile]:
        """根据ID列表获取多个结构化文件"""
        files = await self.find_many({
            "_id": {"$in": [self._convert_id(fid) for fid in file_ids]}
        })
        return [StructureFile(**file) for file in files]

    async def update_structure_file(
        self, 
        file_id: str, 
        excel_content: Optional[bytes] = None,
        json_content: Optional[dict] = None
    ) -> bool:
        """更新结构化文件内容"""
        update_dict = {"updated_at": datetime.now()}
        if excel_content is not None:
            update_dict["excel_content"] = excel_content
        if json_content is not None:
            update_dict["json_content"] = json_content
        
        return await self.update_one(
            {"_id": self._convert_id(file_id)},
            update_dict
        )

    async def delete_structure_file(self, file_id: str) -> bool:
        """删除结构化文件"""
        return await self.delete_one({"_id": self._convert_id(file_id)}) 