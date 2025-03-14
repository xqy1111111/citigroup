from pydantic_settings import BaseSettings
from typing import Optional

class RedisSettings(BaseSettings):
    """Redis配置类"""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_USERNAME: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_ENCODING: str = "utf-8"
    REDIS_POOL_SIZE: int = 10
    REDIS_POOL_TIMEOUT: int = 5

    class Config:
        env_prefix = "REDIS_"  # 环境变量前缀

# 创建配置实例
redis_settings = RedisSettings() 