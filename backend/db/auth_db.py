"""
认证相关的数据库操作模块
包含用于用户身份验证的数据库操作函数
"""
from pymongo import MongoClient
from core.security import verify_password, get_password_hash
from bson.objectid import ObjectId
from datetime import datetime
import os

# 从环境变量获取MongoDB连接字符串
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "myapp")

# 创建MongoDB客户端
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]

def get_user_by_username(username: str):
    """
    通过用户名查找用户
    
    参数:
        username: 用户名
        
    返回:
        dict: 用户文档，如果未找到则返回None
    """
    # 将查询设置为不区分大小写
    # 使用$regex以允许不区分大小写的查询
    return users_collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})

def get_user_by_email(email: str):
    """
    通过电子邮件查找用户
    
    参数:
        email: 电子邮件地址
        
    返回:
        dict: 用户文档，如果未找到则返回None
    """
    # 将查询设置为不区分大小写
    return users_collection.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})

def get_user_by_id(user_id: str):
    """
    通过用户ID查找用户
    
    参数:
        user_id: 用户ID
        
    返回:
        dict: 用户文档，如果未找到则返回None
    """
    # 确保user_id是一个有效的ObjectId
    if not ObjectId.is_valid(user_id):
        return None
    
    return users_collection.find_one({"_id": ObjectId(user_id)})

def create_user(username: str, email: str, password: str, profile_picture: str = None):
    """
    创建新用户
    
    参数:
        username: 用户名
        email: 电子邮件地址
        password: 已哈希的密码
        profile_picture: 用户头像URL（可选）
        
    返回:
        str: 创建的用户ID
    """
    # 创建新用户文档
    user_doc = {
        "username": username,
        "email": email,
        "password": password,  # 假设密码已经在上层被哈希处理
        "profile_picture": profile_picture,
        "repos": [],  # 初始化为空数组
        "collaborations": [],  # 初始化为空数组
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "is_active": True,  # 用户是否激活
        "is_admin": False,  # 用户是否为管理员
    }
    
    # 插入用户文档并返回生成的ID
    result = users_collection.insert_one(user_doc)
    return str(result.inserted_id)

def authenticate_user(username_or_email: str, password: str):
    """
    验证用户凭据
    
    参数:
        username_or_email: 用户名或电子邮件地址
        password: 明文密码
        
    返回:
        str: 用户ID，如果验证失败则返回None
    """
    # 尝试通过用户名查找用户
    user = get_user_by_username(username_or_email)
    
    # 如果未找到，尝试通过电子邮件查找
    if not user:
        user = get_user_by_email(username_or_email)
    
    # 如果仍未找到或密码不匹配，则返回None
    if not user or not verify_password(password, user["password"]):
        return None
    
    # 返回用户ID
    return str(user["_id"])

def update_user_password(user_id: str, new_password: str):
    """
    更新用户密码
    
    参数:
        user_id: 用户ID
        new_password: 新密码（明文）
        
    返回:
        bool: 操作是否成功
    """
    # 确保user_id是一个有效的ObjectId
    if not ObjectId.is_valid(user_id):
        return False
    
    # 对新密码进行哈希处理
    hashed_password = get_password_hash(new_password)
    
    # 更新用户密码和更新时间
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password": hashed_password,
                "updated_at": datetime.now()
            }
        }
    )
    
    # 返回操作是否成功
    return result.modified_count > 0

def deactivate_user(user_id: str):
    """
    停用用户账户
    
    参数:
        user_id: 用户ID
        
    返回:
        bool: 操作是否成功
    """
    # 确保user_id是一个有效的ObjectId
    if not ObjectId.is_valid(user_id):
        return False
    
    # 将用户的is_active字段设置为False
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.now()
            }
        }
    )
    
    # 返回操作是否成功
    return result.modified_count > 0

def reactivate_user(user_id: str):
    """
    重新激活用户账户
    
    参数:
        user_id: 用户ID
        
    返回:
        bool: 操作是否成功
    """
    # 确保user_id是一个有效的ObjectId
    if not ObjectId.is_valid(user_id):
        return False
    
    # 将用户的is_active字段设置为True
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "is_active": True,
                "updated_at": datetime.now()
            }
        }
    )
    
    # 返回操作是否成功
    return result.modified_count > 0 