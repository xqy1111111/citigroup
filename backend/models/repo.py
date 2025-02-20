from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class RepoBase(BaseModel):
    repo_name: str
    
class RepoCreate(RepoBase):
    # repo_name 是必填的
    owner_id: str
    co_user_ids: Optional[List[str]] = []

class RepoInDB(RepoBase):
    repo_id: str = Field(default_factory=lambda: str(ObjectId()))
    owner_id: str
    co_user_ids: List[str] = []
    file_ids: List[str] = []
    structure_file_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Repo(RepoBase):
    repo_id: str
    owner_id: str
    co_user_ids: List[str]
    file_ids: List[str]
    structure_file_ids: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 