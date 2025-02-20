from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from ..database import MongoManager

class BaseRepository:
    def __init__(self, collection_name: str):
        self.db = MongoManager.get_database()
        self.collection: Collection = self.db[collection_name]
    
    async def find_one(self, filter_dict: Dict) -> Optional[Dict]:
        """查找单个文档"""
        return await self.collection.find_one(filter_dict)
    
    async def find_many(self, filter_dict: Dict) -> List[Dict]:
        """查找多个文档"""
        cursor = self.collection.find(filter_dict)
        return await cursor.to_list(length=None)
    
    async def insert_one(self, document: Dict) -> str:
        """插入单个文档"""
        result: InsertOneResult = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def update_one(self, filter_dict: Dict, update_dict: Dict) -> bool:
        """更新单个文档"""
        result: UpdateResult = await self.collection.update_one(
            filter_dict,
            {"$set": update_dict}
        )
        return result.modified_count > 0
    
    async def delete_one(self, filter_dict: Dict) -> bool:
        """删除单个文档"""
        result: DeleteResult = await self.collection.delete_one(filter_dict)
        return result.deleted_count > 0

    def _convert_id(self, id: str) -> ObjectId:
        """转换字符串ID为ObjectId"""
        return ObjectId(id) 