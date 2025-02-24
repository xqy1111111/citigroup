from pydantic import BaseModel
from typing import List, Optional, Dict

# 仓库创建模型
class RepoCreate(BaseModel):
    name: str  # 仓库名称
    desc: str  # 仓库描述

    class Config:
        str_min_length = 1  # 字符串字段最小长度为 1
        str_strip_whitespace = True  # 去除字段的前后空格


# 仓库响应模型
class RepoResponse(BaseModel):
    id: str  # 仓库的 _id
    name: str  # 仓库名称
    desc: str  # 仓库描述
    owner_id: str  # 仓库拥有者的 _id
    collaborators: List[str] = []  # 协作者的 ID 列表
    files: List[Dict] = [] # 文件的 ID 列表
    results: List[Dict] = []  # 处理结果的 ID 列表

    class Config:
        from_attributes = True  # 启用 ORM 模式，支持从 MongoDB 查询结果转化为 Pydantic 模型


# 更新仓库名称和描述的模型
class RepoUpdate(BaseModel):
    new_name: Optional[str] = None  # 新仓库名称（可选）
    new_desc: Optional[str] = None  # 新仓库描述（可选）


# 添加协作者的请求模型
class AddCollaborator(BaseModel):
    collaborator_id: str  # 协作者的 _id
