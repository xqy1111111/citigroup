from fastapi import APIRouter, HTTPException, Request
from core.session import session_manager
from core.rate_limit import rate_limit
from core.redis_manager import redis_manager
from typing import Dict, Any
import time

router = APIRouter()

@router.post("/test/session/create")
async def create_test_session(user_info: Dict[str, Any]):
    """
    创建测试会话
    
    示例请求:
    POST http://localhost:8000/test/session/create
    {
        "user_id": "123",
        "username": "测试用户",
        "email": "test@example.com"
    }
    """
    session_id = await session_manager.create_session(user_info)
    return {"session_id": session_id, "message": "会话创建成功"}

@router.get("/test/session/{session_id}")
async def get_test_session(session_id: str):
    """
    获取会话信息
    
    示例请求:
    GET http://localhost:8000/test/session/{session_id}
    """
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    return session_data

@router.delete("/test/session/{session_id}")
async def delete_test_session(session_id: str):
    """
    删除会话
    
    示例请求:
    DELETE http://localhost:8000/test/session/{session_id}
    """
    success = await session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已删除"}

@router.get("/test/rate-limit")
@rate_limit(limit=5, window=60)  # 60秒内最多允许5次访问
async def test_rate_limit(request: Request):
    """
    测试访问频率限制
    
    示例请求:
    GET http://localhost:8000/test/rate-limit
    
    说明：60秒内只能访问5次，超过限制会返回429错误
    """
    return {"message": "访问成功", "client_ip": request.client.host}

@router.get("/test/cache")
async def test_cache():
    """
    测试Redis缓存功能
    
    示例请求:
    GET http://localhost:8000/test/cache
    """
    cache_key = "test_cache_key"
    
    # 尝试从缓存获取数据
    cached_data = await redis_manager.get_json(cache_key)
    if cached_data:
        return {"message": "从缓存获取的数据", "data": cached_data, "source": "cache"}
    
    # 模拟从数据库获取数据
    new_data = {
        "id": 1,
        "name": "测试数据",
        "timestamp": str(time.time())
    }
    
    # 将数据存入缓存，设置60秒过期
    await redis_manager.set_json(cache_key, new_data, expire=60)
    
    return {"message": "新生成的数据", "data": new_data, "source": "new"} 