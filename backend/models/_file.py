"""
文件数据模型模块

这个模块定义了与文件处理相关的数据模型，包括文件元数据和文件处理结果。
这些模型用于API请求/响应的数据验证，以及与数据库交互时的数据结构定义。

文件系统在本应用中的作用：
1. 允许用户上传各种类型的文件（如文档、音频、图像等）
2. 存储文件的元数据（如名称、大小、上传日期）
3. 跟踪文件处理状态（如上传完成、处理中、处理完成）
4. 关联处理结果与原始文件
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# 移除重复导入
# from pydantic import BaseModel
# from datetime import datetime

class FileMetadata(BaseModel):
    """
    文件元数据模型
    
    存储上传到系统的文件的基本信息，如ID、名称、大小等。
    这个模型用于：
    1. API响应 - 当用户请求文件信息时
    2. 数据库接口 - 从MongoDB检索文件信息时
    3. 前端展示 - 用于展示文件列表和详情
    """
    file_id: str = Field(..., description="文件的唯一标识符，通常是MongoDB GridFS中的ID")
    filename: str = Field(..., description="文件的原始名称，包括扩展名")
    size: int = Field(..., description="文件大小，单位为字节(bytes)")
    upload_date: datetime = Field(..., description="文件上传的日期和时间")
    status: str = Field(..., description="文件当前的处理状态，如'uploaded'、'processing'、'completed'等")
    
    class Config:
        """
        Pydantic模型配置
        """
        # 让模型的字符串表示更加可读
        schema_extra = {
            "example": {
                "file_id": "60d21b4967d0d8992e610c85",
                "filename": "example.mp3",
                "size": 1024000,
                "upload_date": "2023-06-01T12:00:00",
                "status": "uploaded"
            }
        }
        
        # 允许从字典创建模型实例时使用别名字段名
        allow_population_by_field_name = True

class JsonRes(BaseModel):
    """
    JSON结果模型
    
    存储文件处理后生成的JSON格式结果数据。
    例如，音频转写的文本结果、图像分析的标签等。
    
    这个模型通常用于：
    1. 存储处理结果 - 将结构化数据存储到数据库
    2. API响应 - 返回给前端的处理结果
    3. 数据分析 - 对处理结果进行后续分析
    """
    res_id: str = Field(..., description="结果记录的唯一标识符")
    file_id: str = Field(..., description="原始文件的ID，建立结果与源文件的关联")
    content: Dict[str, Any] = Field(..., description="处理结果的具体内容，采用键值对形式存储")
    
    class Config:
        """
        Pydantic模型配置
        """
        schema_extra = {
            "example": {
                "res_id": "60d21b4967d0d8992e610c86",
                "file_id": "60d21b4967d0d8992e610c85",
                "content": {
                    "text": "这是一段转写的文本",
                    "confidence": 0.95,
                    "duration": 120.5
                }
            }
        }
