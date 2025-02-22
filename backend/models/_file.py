from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# models.py
from pydantic import BaseModel
from datetime import datetime

class FileMetadata(BaseModel):
    file_id: str
    filename: str
    size: int
    upload_date: datetime
    status: str
