from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from typing import Optional

class FileBase(BaseModel):
    filename: str
    content: str

class FileCreate(FileBase):
    pass

class FileInDB(FileBase):
    file_id: str = Field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class File(FileBase):
    file_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StructureFileBase(BaseModel):
    excel_content: Optional[bytes]
    json_content: Optional[dict]

class StructureFileCreate(StructureFileBase):
    pass

class StructureFileInDB(StructureFileBase):
    structure_file_id: str = Field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = Field(default_factory=datetime.now)

class StructureFile(StructureFileBase):
    structure_file_id: str
    created_at: datetime

    class Config:
        from_attributes = True 