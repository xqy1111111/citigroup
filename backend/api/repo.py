from fastapi import APIRouter, HTTPException
from models.repo import RepoCreate, RepoResponse, AddCollaborator, RepoUpdate
from db import db_util
from bson import ObjectId

router = APIRouter()

def convert_objectid(obj: Any) -> Any:
    """
    递归转换 MongoDB 查询返回的字典中的所有 ObjectId 为字符串。
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    return obj

def objectID2str(repo: Dict) -> RepoResponse:
    """
    处理 MongoDB 查询返回的 Repo 数据，将所有 ObjectId 转换为字符串
    """
    repo = convert_objectid(repo)  # 深度转换 ObjectId
    return RepoResponse(
        id=repo["_id"],
        name=repo["name"],
        desc=repo["desc"],
        owner_id=repo["owner_id"],
        collaborators=repo.get("collaborators", []),
        files=repo.get("files", []),
        results=repo.get("results", [])
    )

# 创建仓库
@router.post("/", response_model=RepoResponse)
async def create_new_repo(repo: RepoCreate, owner_id: str):
    repo_id = db_util.create_repo(owner_id, repo.name, repo.desc)
    if not repo_id:
        raise HTTPException(status_code=400, detail="Failed to create repo")
    repo_data = db_util.get_repo_by_id(repo_id)
    return objectID2str(repo_data)

# 获取仓库信息
@router.get("/{repo_id}", response_model=RepoResponse)
async def get_repo(repo_id: str):
    repo = db_util.get_repo_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    return objectID2str(repo)

# 更新仓库名称
@router.put("/{repo_id}/name", response_model=str)
async def update_repo_name(repo_id: str, repo_update: RepoUpdate):
    if repo_update.new_name:
        status = db_util.update_repo_name(repo_id, repo_update.new_name)
        if status == "success":
            return "Name updated successfully"
    raise HTTPException(status_code=400, detail="Failed to update repo name")

# 更新仓库描述
@router.put("/{repo_id}/desc", response_model=str)
async def update_repo_desc(repo_id: str, repo_update: RepoUpdate):
    if repo_update.new_desc:
        status = db_util.update_repo_desc(repo_id, repo_update.new_desc)
        if status == "success":
            return "Description updated successfully"
    raise HTTPException(status_code=400, detail="Failed to update repo description")

# 删除仓库
@router.delete("/{repo_id}", response_model=str)
async def delete_repo(repo_id: str):
    status = db_util.delete_repo(repo_id)
    if status == "success":
        return "Repo deleted successfully"
    raise HTTPException(status_code=400, detail="Failed to delete repo")

# 添加协作者
@router.post("/{repo_id}/collaborators", response_model=str)
async def add_collaborator_to_repo(repo_id: str, collaborator: AddCollaborator):
    status = db_util.add_collaborator(repo_id, collaborator.collaborator_id)
    if status == "success":
        return "Collaborator added successfully"
    raise HTTPException(status_code=400, detail="Failed to add collaborator")


# from fastapi import APIRouter, HTTPException
# from models.repo import RepoCreate, RepoResponse, AddCollaborator, RepoUpdate
# from db import db_util as db_util

# router = APIRouter()

# # 创建仓库
# @router.post("/", response_model=RepoResponse)
# async def create_new_repo(repo: RepoCreate, owner_id: str):
#     repo_id = db_util.create_repo(owner_id, repo.name, repo.desc)
#     if not repo_id:
#         raise HTTPException(status_code=400, detail="Failed to create repo")
#     return db_util.get_repo_by_id(repo_id)

# # 获取仓库信息
# @router.get("/{repo_id}", response_model=RepoResponse)
# async def get_repo(repo_id: str):
#     repo = db_util.get_repo_by_id(repo_id)
#     if not repo:
#         raise HTTPException(status_code=404, detail="Repo not found")
#     return repo

# # 更新仓库名称
# @router.put("/{repo_id}/name", response_model=str)
# async def update_repo_name(repo_id: str, repo_update: RepoUpdate):
#     if repo_update.new_name:
#         status = db_util.update_repo_name(repo_id, repo_update.new_name)
#         if status == "success":
#             return "Name updated successfully"
#     raise HTTPException(status_code=400, detail="Failed to update repo name")

# # 更新仓库描述
# @router.put("/{repo_id}/desc", response_model=str)
# async def update_repo_desc(repo_id: str, repo_update: RepoUpdate):
#     if repo_update.new_desc:
#         status = db_util.update_repo_desc(repo_id, repo_update.new_desc)
#         if status == "success":
#             return "Description updated successfully"
#     raise HTTPException(status_code=400, detail="Failed to update repo description")

# # 删除仓库
# @router.delete("/{repo_id}", response_model=str)
# async def delete_repo(repo_id: str):
#     status = delete_repo(repo_id)
#     if status == "success":
#         return "Repo deleted successfully"
#     raise HTTPException(status_code=400, detail="Failed to delete repo")

# # 添加协作者
# @router.post("/{repo_id}/collaborators", response_model=str)
# async def add_collaborator_to_repo(repo_id: str, collaborator: AddCollaborator):
#     status = db_util.add_collaborator(repo_id, collaborator.collaborator_id)
#     if status == "success":
#         return "Collaborator added successfully"
#     raise HTTPException(status_code=400, detail="Failed to add collaborator")
