"""
权限管理模块

这个模块实现了基于角色的访问控制(RBAC)系统，用于保护API端点。

什么是基于角色的访问控制？
--------------------
基于角色的访问控制是一种安全机制，它根据用户的角色(而不是用户身份)来控制对资源的访问权限。
例如：
- 管理员可以访问所有功能
- 普通用户只能访问特定功能
- 游客只能访问公开内容

这种机制比直接指定每个用户的权限更容易管理，特别是当用户数量很多时。

本模块提供：
1. 角色检查 - 验证用户是否拥有特定角色
2. 管理员权限检查 - 验证用户是否为管理员 
3. 资源所有者检查 - 验证用户是否为资源所有者或管理员
"""
from fastapi import Depends, HTTPException, status
from core.security import get_current_user
from db.auth_db import get_user_by_id
from functools import wraps
from typing import List, Callable, Any

# 定义角色常量
# 使用常量而不是字符串可以减少拼写错误，并使代码更容易维护
ROLE_ADMIN = "admin"   # 管理员角色 - 拥有最高权限
ROLE_USER = "user"     # 普通用户角色 - 拥有基本功能权限
ROLE_GUEST = "guest"   # 游客角色 - 只能访问公开内容

def has_role(required_roles: List[str]):
    """
    创建一个依赖项，用于检查当前用户是否具有所需角色
    
    什么是依赖项(Dependency)？
    ---------------------
    在FastAPI中，依赖项是一种可重用的组件，可以在多个API端点中使用。
    当请求到达时，FastAPI会自动解析和执行这些依赖项，然后将结果传递给API处理函数。
    这对于实现认证和授权非常有用。
    
    使用示例:
    ```python
    # 只允许管理员或普通用户访问
    @app.get("/protected", dependencies=[Depends(has_role([ROLE_ADMIN, ROLE_USER]))])
    async def protected_endpoint():
        return {"message": "你有权限访问此端点"}
    ```
    
    参数:
        required_roles: 允许访问的角色列表
        
    返回:
        Callable: 依赖项函数，FastAPI会自动调用它
    """
    async def role_checker(current_user_id: str = Depends(get_current_user)):
        """
        检查当前用户是否具有所需角色
        
        工作流程:
        1. 从令牌中获取当前用户ID
        2. 从数据库查询用户详细信息
        3. 检查用户角色是否在允许的角色列表中
        4. 如果是，允许访问；否则，拒绝访问
        
        参数:
            current_user_id: 当前用户ID，从令牌中获取
            
        返回:
            str: 验证成功后返回用户ID
            
        异常:
            HTTPException 403: 如果用户没有所需角色，抛出"禁止访问"错误
        """
        # 从数据库获取用户详情
        user = get_user_by_id(current_user_id)
        if not user:
            # 用户不存在，可能是令牌有效但用户已被删除
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 获取用户角色
        # 从用户文档中获取role字段，如果没有则默认为"user"角色
        user_role = user.get("role", ROLE_USER)
        
        # 检查管理员特殊权限
        # 如果用户有管理员标志，始终将其角色视为管理员
        if user.get("is_admin", False):
            user_role = ROLE_ADMIN
        
        # 检查用户是否具有所需角色
        # 如果用户的角色不在所需角色列表中，则拒绝访问
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，操作被拒绝"
            )
        
        # 用户角色验证通过，返回用户ID
        return current_user_id
    
    # 返回嵌套的依赖函数
    return role_checker

def is_admin():
    """
    创建一个依赖项，用于检查当前用户是否为管理员
    
    详细说明:
    这是一个特化的角色检查，专门用于验证用户是否具有管理员权限。
    管理员用户拥有系统的最高权限，可以执行所有操作，包括用户管理、
    系统配置等敏感操作。
    
    使用示例:
    ```python
    # 只允许管理员访问的端点
    @app.delete("/users/{user_id}", dependencies=[Depends(is_admin())])
    async def delete_user(user_id: str):
        # 删除用户的逻辑
        pass
    ```
    
    返回:
        Callable: 依赖项函数，FastAPI会自动调用它
    """
    # 直接复用has_role依赖，只允许admin角色
    return has_role([ROLE_ADMIN])

def is_resource_owner(get_owner_id_func: Callable[[Any], str]):
    """
    创建一个依赖项，用于检查当前用户是否为资源所有者或管理员
    
    详细说明:
    这个依赖项用于实现资源级别的访问控制。例如，只有文章的作者
    才能编辑或删除自己的文章。但管理员例外，管理员可以操作任何资源。
    
    工作流程:
    1. 调用提供的函数获取资源所有者ID
    2. 检查当前用户是否为所有者或管理员
    3. 如果是，允许访问；否则，拒绝访问
    
    使用示例:
    ```python
    def get_article_owner(article_id: str):
        article = get_article_by_id(article_id)
        return article["author_id"] if article else None
        
    @app.put("/articles/{article_id}", dependencies=[Depends(is_resource_owner(get_article_owner))])
    async def update_article(article_id: str, article: ArticleUpdate):
        # 更新文章的逻辑
        pass
    ```
    
    参数:
        get_owner_id_func: 一个函数，接收请求参数并返回资源所有者ID
        
    返回:
        Callable: 依赖项函数，FastAPI会自动调用它
    """
    async def owner_checker(current_user_id: str = Depends(get_current_user), **kwargs):
        """
        检查当前用户是否为资源所有者或管理员
        
        详细说明:
        这个函数先获取资源所有者ID，然后比较它与当前用户ID。
        如果不匹配，则检查用户是否为管理员。管理员可以访问
        任何资源，无论其所有者是谁。
        
        参数:
            current_user_id: 当前用户ID，从令牌中获取
            **kwargs: 路径参数和查询参数，将传递给get_owner_id_func
            
        返回:
            str: 验证成功后返回用户ID
            
        异常:
            HTTPException 403: 如果用户既不是资源所有者也不是管理员，抛出"禁止访问"错误
        """
        # 获取资源所有者ID
        resource_owner_id = get_owner_id_func(**kwargs)
        
        # 如果资源不存在
        if resource_owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源不存在"
            )
        
        # 检查当前用户是否为资源所有者
        if current_user_id == resource_owner_id:
            return current_user_id
        
        # 如果不是所有者，检查是否为管理员
        user = get_user_by_id(current_user_id)
        if user and (user.get("role") == ROLE_ADMIN or user.get("is_admin", False)):
            return current_user_id
        
        # 既不是所有者也不是管理员，拒绝访问
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，您不是资源所有者"
        )
    
    # 返回嵌套的依赖函数
    return owner_checker

def require_permission(permission: str):
    """
    创建一个依赖项，用于检查当前用户是否具有特定权限
    
    详细说明:
    这个依赖项实现了细粒度的权限控制，比角色更精确。
    例如，同样是普通用户，可能有些用户有创建项目的权限，
    有些用户只有查看权限。这种机制允许在角色的基础上
    进一步细化权限控制。
    
    工作流程:
    1. 从令牌中获取当前用户ID
    2. 从数据库查询用户详细信息，包括其权限列表
    3. 检查用户是否拥有所需权限
    4. 如果有，允许访问；否则，拒绝访问
    
    使用示例:
    ```python
    # 需要"create_project"权限的端点
    @app.post("/projects", dependencies=[Depends(require_permission("create_project"))])
    async def create_project(project: ProjectCreate):
        # 创建项目的逻辑
        pass
    ```
    
    参数:
        permission: 访问所需的权限标识符
        
    返回:
        Callable: 依赖项函数，FastAPI会自动调用它
    """
    async def permission_checker(current_user_id: str = Depends(get_current_user)):
        """
        检查当前用户是否具有特定权限
        
        详细说明:
        此函数会查询用户记录以获取其权限列表，然后检查所需权限
        是否在列表中。管理员自动拥有所有权限。
        
        参数:
            current_user_id: 当前用户ID，从令牌中获取
            
        返回:
            str: 验证成功后返回用户ID
            
        异常:
            HTTPException 403: 如果用户没有所需权限，抛出"禁止访问"错误
        """
        # 从数据库获取用户信息
        user = get_user_by_id(current_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查管理员权限 - 管理员拥有所有权限
        if user.get("role") == ROLE_ADMIN or user.get("is_admin", False):
            return current_user_id
        
        # 获取用户权限列表
        user_permissions = user.get("permissions", [])
        
        # 检查用户是否具有所需权限
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 '{permission}' 权限"
            )
        
        # 权限验证通过
        return current_user_id
    
    # 返回嵌套的依赖函数
    return permission_checker

def require_any_permission(permissions: List[str]):
    """
    创建一个依赖项，用于检查当前用户是否具有指定权限列表中的任意一个
    
    详细说明:
    与require_permission不同，这个依赖项允许指定多个权限，只要用户
    拥有其中任意一个权限即可通过验证。这在某些功能有多个访问路径时很有用。
    
    使用示例:
    ```python
    # 需要"manage_users"或"view_reports"权限的端点
    @app.get("/user-reports", dependencies=[Depends(require_any_permission(["manage_users", "view_reports"]))])
    async def get_user_reports():
        # 获取用户报告的逻辑
        pass
    ```
    
    参数:
        permissions: 访问所需的权限标识符列表（用户只需拥有其中一个）
        
    返回:
        Callable: 依赖项函数，FastAPI会自动调用它
    """
    async def permission_checker(current_user_id: str = Depends(get_current_user)):
        """
        检查当前用户是否具有指定权限列表中的任意一个
        
        详细说明:
        此函数获取用户的权限列表，然后检查是否与所需权限有交集。
        只要有一个权限匹配，就允许访问。管理员自动拥有所有权限。
        
        参数:
            current_user_id: 当前用户ID，从令牌中获取
            
        返回:
            str: 验证成功后返回用户ID
            
        异常:
            HTTPException 403: 如果用户没有任何所需权限，抛出"禁止访问"错误
        """
        # 从数据库获取用户信息
        user = get_user_by_id(current_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查管理员权限 - 管理员拥有所有权限
        if user.get("role") == ROLE_ADMIN or user.get("is_admin", False):
            return current_user_id
        
        # 获取用户权限列表
        user_permissions = set(user.get("permissions", []))
        
        # 检查是否有任意一个所需权限
        if not user_permissions.intersection(set(permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下权限之一: {', '.join(permissions)}"
            )
        
        # 权限验证通过
        return current_user_id
    
    # 返回嵌套的依赖函数
    return permission_checker

def require_all_permissions(permissions: List[str]):
    """
    创建一个依赖项，用于检查当前用户是否具有指定的所有权限
    
    详细说明:
    这个依赖项要求用户必须同时拥有所有指定的权限才能访问资源。
    这适用于需要多种权限组合的高安全性操作，确保只有那些获得
    完整授权的用户才能执行操作。
    
    使用示例:
    ```python
    # 需要同时拥有"manage_users"和"delete_data"权限的端点
    @app.delete("/users/{user_id}/data", dependencies=[Depends(require_all_permissions(["manage_users", "delete_data"]))])
    async def delete_user_data(user_id: str):
        # 删除用户数据的逻辑
        pass
    ```
    
    参数:
        permissions: 访问所需的所有权限标识符列表
        
    返回:
        Callable: 依赖项函数，FastAPI会自动调用它
    """
    async def permission_checker(current_user_id: str = Depends(get_current_user)):
        """
        检查当前用户是否具有所有指定权限
        
        详细说明:
        此函数获取用户的权限列表，然后检查是否包含所有所需权限。
        必须完全匹配所有权限才允许访问。管理员自动拥有所有权限。
        
        参数:
            current_user_id: 当前用户ID，从令牌中获取
            
        返回:
            str: 验证成功后返回用户ID
            
        异常:
            HTTPException 403: 如果用户缺少任何所需权限，抛出"禁止访问"错误
        """
        # 从数据库获取用户信息
        user = get_user_by_id(current_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查管理员权限 - 管理员拥有所有权限
        if user.get("role") == ROLE_ADMIN or user.get("is_admin", False):
            return current_user_id
        
        # 获取用户权限列表
        user_permissions = set(user.get("permissions", []))
        
        # 检查是否包含所有所需权限
        missing_permissions = set(permissions) - user_permissions
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，缺少以下权限: {', '.join(missing_permissions)}"
            )
        
        # 权限验证通过
        return current_user_id
    
    # 返回嵌套的依赖函数
    return permission_checker

# 辅助函数：检查用户是否具有特定范围
def check_scopes(user_scopes: List[str], required_scopes: List[str]) -> bool:
    """
    检查用户是否具有所需的权限范围
    
    这个函数实现了基于范围(Scope)的细粒度权限检查。
    范围是比角色更细粒度的权限控制，允许指定用户可以执行的具体操作。
    例如: read:users, write:repos, delete:files 等。
    
    示例:
    ```python
    user_scopes = ["read:users", "write:repos"]
    # 检查用户是否可以读取用户信息
    can_read_users = check_scopes(user_scopes, ["read:users"])  # 返回 True
    # 检查用户是否可以删除文件
    can_delete_files = check_scopes(user_scopes, ["delete:files"])  # 返回 False
    ```
    
    参数:
        user_scopes: 用户拥有的权限范围列表
        required_scopes: 所需的权限范围列表
        
    返回:
        bool: 如果用户具有所有所需的权限范围，则返回True
    """
    # all() 函数检查列表中的所有元素是否都为True
    # 这里检查required_scopes中的每个范围是否都在user_scopes中
    return all(scope in user_scopes for scope in required_scopes) 