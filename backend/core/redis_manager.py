from redis import asyncio as aioredis
from typing import Optional
from .config.redis_config import redis_settings
from core.logging import logger

class RedisManager:
    """Redis连接管理器"""
    _instance: Optional['RedisManager'] = None
    _redis = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def init_redis_pool(self):
        """初始化Redis连接池"""
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}",
                    db=redis_settings.REDIS_DB,
                    password=redis_settings.REDIS_PASSWORD,
                    username=redis_settings.REDIS_USERNAME,
                    encoding=redis_settings.REDIS_ENCODING,
                    ssl=redis_settings.REDIS_SSL,
                    max_connections=redis_settings.REDIS_POOL_SIZE,
                    socket_timeout=redis_settings.REDIS_POOL_TIMEOUT
                )
                logger.info("Redis连接池初始化成功")
            except Exception as e:
                logger.error(f"Redis连接池初始化失败: {str(e)}")
                raise

    async def close(self):
        """关闭Redis连接池"""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.info("Redis连接池已关闭")

    @property
    def redis(self):
        """获取Redis客户端实例"""
        if self._redis is None:
            raise RuntimeError("Redis连接池未初始化")
        return self._redis

    # 常用的Redis操作方法
    async def set(self, key: str, value: str, expire: int = None):
        """设置键值对"""
        await self.redis.set(key, value, ex=expire)

    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        return await self.redis.get(key)

    async def delete(self, key: str):
        """删除键"""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.redis.exists(key)

    async def set_json(self, key: str, value: dict, expire: int = None):
        """存储JSON数据"""
        import json
        await self.redis.set(key, json.dumps(value), ex=expire)

    async def get_json(self, key: str) -> Optional[dict]:
        """获取JSON数据"""
        import json
        data = await self.redis.get(key)
        return json.loads(data) if data else None

# 创建全局Redis管理器实例
redis_manager = RedisManager() 