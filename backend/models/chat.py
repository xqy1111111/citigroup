"""
聊天数据模型模块

这个模块定义了聊天系统所需的数据模型，使用Pydantic库实现数据验证和序列化。

什么是Pydantic？
--------------
Pydantic是一个用于数据验证和设置管理的Python库。它提供了以下功能：
1. 数据验证 - 确保数据符合预定义的类型和约束
2. 数据转换 - 自动将输入数据转换为正确的类型
3. JSON序列化 - 轻松将模型转换为JSON
4. 文档生成 - 自动为API生成清晰的文档

为什么使用Pydantic？
- 类型安全：捕获类型错误
- 清晰的代码：模型结构一目了然
- 自动验证：减少手动检查代码
"""
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from bson import ObjectId

class MessageBase(BaseModel):
    """
    消息的基础模型
    
    定义了一条消息的基本结构，包括发送者、内容和时间戳。
    作为其他消息相关模型的基类。
    """
    sayer: str = Field(..., description="消息发送者，可以是'user'(用户)或'assistant'(助手)")
    text: str = Field(..., description="消息的文本内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息的发送时间，默认为当前时间")

class Message(MessageBase):
    """
    完整的消息模型
    
    继承自MessageBase，目前没有添加额外字段，
    但将来可以在不修改基础模型的情况下扩展功能。
    """
    pass


class text(BaseModel):  # 保持原始类名为小写，虽然不符合Python命名规范，但保持代码兼容性
    """
    对话文本模型
    
    表示一个完整的对话单元，包含一个问题(用户消息)和一个回答(助手消息)。
    """
    question: Message = Field(..., description="用户提出的问题")
    answer: Message = Field(..., description="系统生成的回答")

class ChatHistory(BaseModel):
    """
    聊天历史记录模型
    
    存储特定用户与特定仓库之间的完整对话历史。
    包含用户ID、仓库ID和所有对话文本列表。
    
    这个模型用于数据库存储和API响应，允许前端展示完整的聊天记录。
    """
    user_id: str = Field(..., description="聊天历史所属的用户ID")
    repo_id: str = Field(..., description="聊天历史关联的仓库ID")
    texts: List[text] = [] # 恢复原始的空列表初始化方式
    _id: str = Field(..., description="MongoDB文档ID")
    
    class Config:
        """
        模型配置
        
        Pydantic的特殊类，用于配置模型的行为。
        """
        # 允许任意类型，对于处理MongoDB的ObjectId等特殊类型很有用
        arbitrary_types_allowed = True
        
        # 允许通过别名访问字段，有助于处理数据库字段名与模型字段名不同的情况
        allow_population_by_field_name = True


    
