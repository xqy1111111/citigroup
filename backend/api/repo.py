"""
仓库API路由模块

这个模块实现了与仓库(Repo)相关的所有API端点，包括：
1. 创建仓库 - 为用户创建新的文件仓库
2. 获取仓库信息 - 查询仓库详情
3. 更新仓库 - 修改仓库名称或描述
4. 删除仓库 - 完全删除仓库及其内容
5. 协作者管理 - 添加协作者到仓库

仓库是本系统的核心组织单位，用于存储和管理用户上传的文件及其处理结果。
"""
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from models.repo import RepoCreate, RepoResponse, AddCollaborator, RepoUpdate
from db import db_util
from bson import ObjectId

# 创建路由器实例
router = APIRouter()

def convert_objectid(obj: Any):
    """
    递归转换MongoDB返回的数据中的ObjectId为字符串
    
    详细说明:
    MongoDB使用ObjectId作为文档的唯一标识符，但JSON不支持这种类型。
    这个函数递归遍历数据结构(列表、字典等)，将所有ObjectId转换为字符串。
    
    工作原理:
    1. 如果是ObjectId，直接转为字符串
    2. 如果是列表，递归处理每个元素
    3. 如果是字典，递归处理每个值
    4. 其他类型直接返回字符串表示
    
    参数:
        obj: Any - 要处理的数据对象，可以是任何类型
        
    返回:
        转换后的数据，所有ObjectId都变成了字符串
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    return str(obj)

def objectID2str(repo: Dict) -> RepoResponse:
    """
    处理MongoDB返回的仓库数据，转换为API响应格式
    
    详细说明:
    将数据库返回的原始仓库文档转换为符合RepoResponse模型的格式。
    处理过程包含两步：
    1. 调用convert_objectid深度转换所有ObjectId
    2. 构建RepoResponse对象，确保字段名称和类型正确
    
    参数:
        repo: Dict - MongoDB返回的仓库文档
        
    返回:
        RepoResponse - 符合API响应格式的仓库数据
    """
    repo = convert_objectid(repo)  # 深度转换ObjectId为字符串
    print(repo)  # 调试输出，帮助开发者检查转换结果
    
    # 构建并返回符合RepoResponse模型的对象
    return RepoResponse(
        id=repo["_id"],  # 仓库ID
        name=repo["name"],  # 仓库名称
        desc=repo["desc"],  # 仓库描述
        owner_id=repo["owner_id"],  # 仓库所有者ID
        collaborators=repo.get("collaborators", []),  # 协作者ID列表，不存在则提供空列表
        files=repo.get("files", []),  # 文件列表，不存在则提供空列表
        results=repo.get("results", [])  # 结果列表，不存在则提供空列表
    )

# 创建仓库
@router.post("/", response_model=RepoResponse)
async def create_new_repo(repo: RepoCreate, owner_id: str):
    """
    创建新仓库API
    
    详细说明:
    此端点用于为特定用户创建一个新的仓库。
    仓库是存储和组织文件与处理结果的容器。
    
    流程:
    1. 接收仓库名称、描述和所有者ID
    2. 调用数据库函数创建仓库
    3. 获取并返回创建的仓库详情
    
    参数:
        repo: RepoCreate - 包含仓库名称和描述的请求体
        owner_id: str - 仓库所有者的用户ID
        
    返回:
        RepoResponse - 创建成功的仓库详情
        
    错误:
        400 Bad Request - 创建仓库失败，可能是名称已存在或其他数据库错误
    """
    # 调用数据库工具函数创建仓库
    repo_id = db_util.create_repo(owner_id, repo.name, repo.desc)
    
    # 检查创建是否成功
    if not repo_id:
        raise HTTPException(status_code=400, detail="Failed to create repo")
    
    # 获取并返回创建的仓库详情
    repo_data = db_util.get_repo_by_id(repo_id)
    return objectID2str(repo_data)

# 获取仓库信息
@router.get("/{repo_id}", response_model=RepoResponse)
async def get_repo(repo_id: str):
    """
    获取仓库详情API
    
    详细说明:
    此端点根据仓库ID获取仓库的详细信息，包括基本信息、
    协作者列表、文件列表和处理结果列表。
    
    流程:
    1. 接收仓库ID参数
    2. 调用数据库函数查询仓库
    3. 转换并返回仓库详情
    
    参数:
        repo_id: str - 仓库的唯一标识符
        
    返回:
        RepoResponse - 仓库的详细信息
        
    错误:
        404 Not Found - 如果指定ID的仓库不存在
    """
    # 调用数据库工具函数获取仓库信息
    repo = db_util.get_repo_by_id(repo_id)
    
    # 如果仓库不存在，抛出404错误
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    
    # 转换并返回仓库信息
    return objectID2str(repo)

# 更新仓库名称
@router.put("/{repo_id}/name", response_model=str)
async def update_repo_name(repo_id: str, repo_update: RepoUpdate):
    """
    更新仓库名称API
    
    详细说明:
    此端点用于修改指定仓库的名称。
    仓库名称在同一用户下必须唯一。
    
    流程:
    1. 接收仓库ID和新名称
    2. 验证新名称是否提供
    3. 调用数据库函数更新仓库名称
    
    参数:
        repo_id: str - 要更新的仓库ID
        repo_update: RepoUpdate - 包含新名称的请求体
        
    返回:
        str - 成功消息
        
    错误:
        400 Bad Request - 更新失败，可能是新名称已存在或未提供
    """
    # 检查是否提供了新名称
    if repo_update.new_name:
        # 调用数据库工具函数更新仓库名称
        status = db_util.update_repo_name(repo_id, repo_update.new_name)
        
        # 检查更新是否成功
        if status == "success":
            return "Name updated successfully"
    
    # 如果未提供新名称或更新失败，抛出400错误
    raise HTTPException(status_code=400, detail="Failed to update repo name")

# 更新仓库描述
@router.put("/{repo_id}/desc", response_model=str)
async def update_repo_desc(repo_id: str, repo_update: RepoUpdate):
    """
    更新仓库描述API
    
    详细说明:
    此端点用于修改指定仓库的描述。
    描述用于说明仓库的用途和内容。
    
    流程:
    1. 接收仓库ID和新描述
    2. 验证新描述是否提供
    3. 调用数据库函数更新仓库描述
    
    参数:
        repo_id: str - 要更新的仓库ID
        repo_update: RepoUpdate - 包含新描述的请求体
        
    返回:
        str - 成功消息
        
    错误:
        400 Bad Request - 更新失败，可能是新描述未提供
    """
    # 检查是否提供了新描述
    if repo_update.new_desc:
        # 调用数据库工具函数更新仓库描述
        status = db_util.update_repo_desc(repo_id, repo_update.new_desc)
        
        # 检查更新是否成功
        if status == "success":
            return "Description updated successfully"
    
    # 如果未提供新描述或更新失败，抛出400错误
    raise HTTPException(status_code=400, detail="Failed to update repo description")

# 删除仓库
@router.delete("/{repo_id}", response_model=str)
async def delete_repo(repo_id: str):
    """
    删除仓库API
    
    详细说明:
    此端点用于完全删除指定的仓库，包括其所有文件和处理结果。
    这是一个不可逆操作，删除后的数据无法恢复。
    
    流程:
    1. 接收仓库ID
    2. 调用数据库函数删除仓库
    3. 返回删除结果
    
    参数:
        repo_id: str - 要删除的仓库ID
        
    返回:
        str - 成功消息
        
    错误:
        400 Bad Request - 删除失败，可能是仓库不存在或权限问题
    """
    # 调用数据库工具函数删除仓库
    status = db_util.delete_repo(repo_id)
    
    # 检查删除是否成功
    if status == "success":
        return "Repo deleted successfully"
    
    # 如果删除失败，抛出400错误
    raise HTTPException(status_code=400, detail="Failed to delete repo")

# 添加协作者
@router.post("/{repo_id}/collaborators", response_model=str)
async def add_collaborator_to_repo(repo_id: str, collaborator: AddCollaborator):
    """
    添加仓库协作者API
    
    详细说明:
    此端点用于向仓库添加协作者，使其他用户可以访问和操作仓库内容。
    协作者可以查看、上传和处理文件，但不能删除仓库或修改其基本信息。
    
    流程:
    1. 接收仓库ID和协作者ID
    2. 调用数据库函数添加协作关系
    3. 返回添加结果
    
    参数:
        repo_id: str - 仓库ID
        collaborator: AddCollaborator - 包含协作者ID的请求体
        
    返回:
        str - 成功消息
        
    错误:
        400 Bad Request - 添加失败，可能是用户或仓库不存在，或用户已是协作者
    """
    # 调用数据库工具函数添加协作者
    status = db_util.add_collaborator(repo_id, collaborator.collaborator_id)
    
    # 检查添加是否成功
    if status == "success":
        return "Collaborator added successfully"
    
    # 如果添加失败，抛出400错误
    raise HTTPException(status_code=400, detail="Failed to add collaborator")
