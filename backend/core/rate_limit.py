from core.redis_manager import redis_manager
from fastapi import HTTPException
import time
from typing import Optional

class RateLimiter:
    """访问频率限制器"""
    
    def __init__(self, prefix: str = "rate_limit:", default_limit: int = 60, default_window: int = 60):
        """
        初始化频率限制器
        
        Args:
            prefix: Redis键前缀
            default_limit: 默认时间窗口内的最大请求次数
            default_window: 默认时间窗口（秒）
        """
        self.prefix = prefix
        self.default_limit = default_limit
        self.default_window = default_window
    
    def _get_key(self, identifier: str) -> str:
        """获取完整的Redis键名"""
        return f"{self.prefix}{identifier}"
    
    async def is_allowed(self, identifier: str, limit: Optional[int] = None, window: Optional[int] = None) -> bool:
        """
        检查请求是否允许通过
        
        Args:
            identifier: 限制对象的标识（如IP地址或用户ID）
            limit: 时间窗口内的最大请求次数
            window: 时间窗口（秒）
            
        Returns:
            bool: 是否允许请求通过
        """
        limit = limit or self.default_limit
        window = window or self.default_window
        
        key = self._get_key(identifier)
        current_time = int(time.time())
        
        # 获取当前计数
        count = await redis_manager.get(key)
        if count is None:
            # 第一次访问
            await redis_manager.set(key, "1", expire=window)
            return True
            
        count = int(count)
        if count >= limit:
            return False
            
        # 增加计数
        await redis_manager.set(key, str(count + 1), expire=window)
        return True
    
    async def get_remaining(self, identifier: str, limit: Optional[int] = None) -> int:
        """
        获取剩余的可用请求次数
        
        Args:
            identifier: 限制对象的标识
            limit: 时间窗口内的最大请求次数
            
        Returns:
            int: 剩余的可用请求次数
        """
        limit = limit or self.default_limit
        key = self._get_key(identifier)
        count = await redis_manager.get(key)
        
        if count is None:
            return limit
        
        return max(0, limit - int(count))

# 创建全局频率限制器实例
rate_limiter = RateLimiter()

# FastAPI中间件装饰器
def rate_limit(limit: Optional[int] = None, window: Optional[int] = None):
    """
    频率限制装饰器
    
    用法示例：
    @app.get("/api/endpoint")
    @rate_limit(limit=100, window=60)  # 60秒内最多100次请求
    async def endpoint():
        return {"message": "Hello"}
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if hasattr(arg, "client"):
                    request = arg
                    break
            
            if request is None:
                raise ValueError("无法获取请求对象")
            
            # 使用客户端IP作为标识
            identifier = request.client.host
            
            # 检查是否允许请求
            if not await rate_limiter.is_allowed(identifier, limit, window):
                remaining = await rate_limiter.get_remaining(identifier, limit)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": "请求过于频繁，请稍后再试",
                        "remaining": remaining,
                        "reset_after": window
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator 