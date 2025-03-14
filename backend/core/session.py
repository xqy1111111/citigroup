from core.redis_manager import redis_manager
from typing import Optional, Dict, Any
import json
import time
from uuid import uuid4

class SessionManager:
    """用户会话管理器"""
    
    def __init__(self, prefix: str = "session:", expire_time: int = 3600 * 24):
        """
        初始化会话管理器
        
        Args:
            prefix: Redis键前缀
            expire_time: 会话过期时间（秒），默认24小时
        """
        self.prefix = prefix
        self.expire_time = expire_time
    
    def _get_key(self, session_id: str) -> str:
        """获取完整的Redis键名"""
        return f"{self.prefix}{session_id}"
    
    async def create_session(self, user_data: Dict[str, Any]) -> str:
        """
        创建新的会话
        
        Args:
            user_data: 用户数据字典
            
        Returns:
            str: 会话ID
        """
        session_id = str(uuid4())
        session_data = {
            "user_data": user_data,
            "created_at": int(time.time()),
            "last_accessed": int(time.time())
        }
        
        await redis_manager.set_json(
            self._get_key(session_id),
            session_data,
            expire=self.expire_time
        )
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict]: 会话数据，如果会话不存在则返回None
        """
        session_data = await redis_manager.get_json(self._get_key(session_id))
        if session_data:
            # 更新最后访问时间
            session_data["last_accessed"] = int(time.time())
            await redis_manager.set_json(
                self._get_key(session_id),
                session_data,
                expire=self.expire_time
            )
            return session_data
        return None
    
    async def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """
        更新会话数据
        
        Args:
            session_id: 会话ID
            user_data: 新的用户数据
            
        Returns:
            bool: 更新是否成功
        """
        session_data = await self.get_session(session_id)
        if session_data:
            session_data["user_data"].update(user_data)
            session_data["last_accessed"] = int(time.time())
            await redis_manager.set_json(
                self._get_key(session_id),
                session_data,
                expire=self.expire_time
            )
            return True
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        key = self._get_key(session_id)
        if await redis_manager.exists(key):
            await redis_manager.delete(key)
            return True
        return False

# 创建全局会话管理器实例
session_manager = SessionManager() 