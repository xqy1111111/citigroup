from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 文件元数据响应模型
class FileMetadata(BaseModel):
    file_id: str
    filename: str
    size: int
    upload_date: datetime  # 上传日期
    status: Optional[str] = "unknown"  # 文件状态，默认为 "unknown"

    class Config:
        from_attributes = True  # 支持从 MongoDB 查询结果转化为 Pydantic 模型


# 文件上传请求模型
class FileUpload(BaseModel):
    repo_id: str  # 仓库 ID
    filename: str  # 文件名
    source: bool = True  # 如果 source=True 则更新 files 列表，否则更新 results 列表

# 文件状态更新请求模型
class FileStatusUpdate(BaseModel):
    status: str  # 文件的新状态，默认为 "complete"
    source: bool = True  # 如果 source=True，则更新 files，否则更新 results
