"""
仓库数据模型模块

这个模块定义了与文件仓库相关的数据模型，包括仓库创建、查询和更新。
仓库是本系统的核心概念，它是文件和处理结果的容器，支持多用户协作。

仓库系统的主要功能:
1. 存储和组织用户上传的文件
2. 记录文件处理的结果
3. 支持多用户协作处理文件
4. 管理不同文件之间的关联关系
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# 仓库创建模型
class RepoCreate(BaseModel):
    """
    仓库创建模型
    
    用于创建新仓库时验证请求数据。
    每个用户可以创建多个仓库，但仓库名称在同一用户下必须唯一。
    """
    name: str = Field(..., description="仓库名称，在同一用户下必须唯一", min_length=1, max_length=100)
    desc: str = Field(..., description="仓库描述，说明仓库的用途和内容", min_length=1)

    class Config:
        """
        模型配置
        """
        str_min_length = 1  # 字符串字段最小长度为 1，防止空字符串
        str_strip_whitespace = True  # 自动去除字符串字段的前后空格
        
        # 添加示例数据
        schema_extra = {
            "example": {
                "name": "项目文档",
                "desc": "存储与项目相关的所有文档和处理结果"
            }
        }


# 仓库响应模型
class RepoResponse(BaseModel):
    """
    仓库响应模型
    
    用于返回仓库详细信息。
    包含仓库的基本信息、协作者列表、文件列表和处理结果列表。
    
    这个模型用于:
    1. 获取单个仓库详情API
    2. 获取仓库列表API
    3. 创建或更新仓库后的响应
    """
    id: str = Field(..., description="仓库在数据库中的唯一标识符")
    name: str = Field(..., description="仓库名称")
    desc: str = Field(..., description="仓库描述")
    owner_id: str = Field(..., description="仓库所有者的用户ID")
    collaborators: List[str] = []
    files: List[Dict] = []
    results: List[Dict] = []

    class Config:
        """
        模型配置
        """
        from_attributes = True  # 启用ORM模式，支持从数据库对象转换
        
        # 添加示例数据
        schema_extra = {
            "example": {
                "id": "60d21b4967d0d8992e610c85",
                "name": "项目文档",
                "desc": "存储与项目相关的所有文档和处理结果",
                "owner_id": "60d21b4967d0d8992e610c86",
                "collaborators": ["60d21b4967d0d8992e610c87"],
                "files": [
                    {
                        "file_id": "60d21b4967d0d8992e610c88",
                        "filename": "document.pdf",
                        "size": 1024000,
                        "uploaded_at": "2023-06-01T12:00:00",
                        "status": "processed"
                    }
                ],
                "results": [
                    {
                        "file_id": "60d21b4967d0d8992e610c89",
                        "source_file": "60d21b4967d0d8992e610c88",
                        "filename": "document_text.txt",
                        "size": 10240,
                        "uploaded_at": "2023-06-01T12:05:00",
                        "status": "completed"
                    }
                ]
            }
        }


# 更新仓库名称和描述的模型
class RepoUpdate(BaseModel):
    """
    仓库更新模型
    
    用于更新仓库信息。
    所有字段都是可选的，只更新提供的字段。
    
    使用场景:
    - 修改仓库名称
    - 更新仓库描述
    - 其他仓库属性的部分更新
    """
    new_name: Optional[str] = Field(None, description="新的仓库名称，不提供则保持不变")
    new_desc: Optional[str] = Field(None, description="新的仓库描述，不提供则保持不变")
    
    class Config:
        """模型配置"""
        schema_extra = {
            "example": {
                "new_name": "新项目文档",
                "new_desc": "更新后的项目描述"
            }
        }


# 添加协作者的请求模型
class AddCollaborator(BaseModel):
    """
    添加协作者模型
    
    用于向仓库添加协作者的请求验证。
    
    协作机制:
    1. 仓库所有者可以添加多个协作者
    2. 协作者可以访问仓库中的文件和结果
    3. 协作者可以上传文件和处理文件
    4. 但协作者无法删除仓库或修改仓库基本信息
    """
    collaborator_id: str = Field(..., description="要添加的协作者用户ID")
    
    class Config:
        """模型配置"""
        schema_extra = {
            "example": {
                "collaborator_id": "60d21b4967d0d8992e610c87"
            }
        }
