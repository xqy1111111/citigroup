from pydantic_settings import BaseSettings
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database

class Settings(BaseSettings):
    # 数据库配置
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "your_database_name"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件处理配置
    SOURCE_DATA_DIR: str = "DataStructuring/DataStructuring/SourceData"
    TARGET_DATA_DIR: str = "DataStructuring/DataStructuring/TargetData"
    
    # 文件存储设置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # MongoDB客户端和数据库实例
    _mongodb_client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    @property
    def mongodb_client(self) -> MongoClient:
        if not self._mongodb_client:
            self._mongodb_client = MongoClient(self.MONGODB_URL)
        return self._mongodb_client
    
    @property
    def database(self) -> Database:
        if not self._database:
            self._database = self.mongodb_client[self.DATABASE_NAME]
        return self._database
    
    class Config:
        env_file = ".env"

settings = Settings() 