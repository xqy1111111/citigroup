from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from ..config.settings import settings
from typing import Optional

class MongoManager:
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[Database] = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls._client is None:
            cls._client = AsyncIOMotorClient(settings.MONGODB_URL)
        return cls._client

    @classmethod
    def get_database(cls) -> Database:
        if cls._db is None:
            cls._db = cls.get_client()[settings.DATABASE_NAME]
        return cls._db

    @classmethod
    async def close_connections(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """连接数据库"""
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        
    @classmethod
    async def close_db(cls):
        """关闭数据库连接"""
        if cls.client:
            await cls.client.close()
    
    @classmethod
    def get_db(cls):
        """获取数据库实例"""
        return cls.client[settings.DATABASE_NAME] 