"""
权限管理模块
提供基于角色的访问控制功能
"""
from fastapi import Depends, HTTPException, status
from core.security import get_current_user
from db.auth_db import get_user_by_id
from functools import wraps
from typing import List, Callable, Any

# 定义角色常量
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_GUEST = "guest"

def has_role(required_roles: List[str]):
    """
    创建一个依赖项，用于检查当前用户是否具有所需角色
    
    参数:
        required_roles: 允许访问的角色列表
        
    返回:
        Callable: 依赖项函数
    """
    async def role_checker(current_user_id: str = Depends(get_current_user)):
        """
        检查当前用户是否具有所需角色
        
        参数:
            current_user_id: 当前用户ID，从令牌中获取
            
        返回:
            str: 当前用户ID
            
        异常:
            HTTPException 403: 如果用户没有所需角色
        """
        # 从数据库获取用户详情
        user = get_user_by_id(current_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 获取用户角色
        # 这里假设用户文档中有一个role字段
        # 如果没有，则默认为"user"角色
        user_role = user.get("role", ROLE_USER)
        
        # 检查管理员特殊权限
        if user.get("is_admin", False):
            user_role = ROLE_ADMIN
        
        # 检查用户是否具有所需角色
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，操作被拒绝"
            )
        
        # 返回用户ID
        return current_user_id
    
    return role_checker

def admin_required(func: Callable) -> Callable:
    """
    要求管理员权限的装饰器
    
    参数:
        func: 要装饰的函数
        
    返回:
        Callable: 装饰后的函数
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 检查current_user参数是否在kwargs中
        if "current_user" not in kwargs:
            raise ValueError("装饰的函数必须有current_user参数")
        
        current_user_id = kwargs["current_user"]
        user = get_user_by_id(current_user_id)
        
        # 检查用户是否为管理员
        if not user or not user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        
        # 调用原始函数
        return await func(*args, **kwargs)
    
    return wrapper

def resource_owner_or_admin(resource_owner_getter: Callable[[Any], str]):
    """
    创建一个装饰器，要求当前用户是资源所有者或管理员
    
    参数:
        resource_owner_getter: 从资源获取所有者ID的函数
        
    返回:
        Callable: 装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查current_user参数是否在kwargs中
            if "current_user" not in kwargs:
                raise ValueError("装饰的函数必须有current_user参数")
            
            current_user_id = kwargs["current_user"]
            user = get_user_by_id(current_user_id)
            
            # 获取资源
            # 这里假设资源ID在kwargs中
            # 实际应用中需要根据具体情况修改
            resource_id = kwargs.get("resource_id")
            if not resource_id:
                raise ValueError("找不到资源ID参数")
            
            # 获取资源所有者ID
            owner_id = resource_owner_getter(resource_id)
            
            # 检查用户是否为资源所有者或管理员
            if current_user_id != owner_id and not user.get("is_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="您没有权限访问此资源"
                )
            
            # 调用原始函数
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

# 辅助函数：检查用户是否具有特定范围
def check_scopes(user_scopes: List[str], required_scopes: List[str]) -> bool:
    """
    检查用户是否具有所需的权限范围
    
    参数:
        user_scopes: 用户拥有的权限范围列表
        required_scopes: 所需的权限范围列表
        
    返回:
        bool: 如果用户具有所有所需的权限范围，则返回True
    """
    return all(scope in user_scopes for scope in required_scopes) 