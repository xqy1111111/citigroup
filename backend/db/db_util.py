import os
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
from gridfs import GridFS
from datetime import datetime, UTC
from db import db_config
from models.chat import Message

# 初始化MongoDB客户端
client = MongoClient(db_config.DB_URL)
db = client.file_processing_app
fs = GridFS(db)

# =============================== 用户相关操作 ===============================

# 创建新用户
def create_user(username, email, password, profile_picture=None):
    """
    创建一个新的用户，
    :param username 用户名
    :param email 邮箱
    :param password 明文密码
    :param profile_picture 头像(可选)
    :return: 返回用户的 mongodb _id
    """
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "profile_picture": profile_picture,
        "repos": [],
        "collaborations": []
    }
    result = db.users.insert_one(user)
    return str(result.inserted_id)

def authenticate_user(username_or_email, password):
    """
    验证用户名或邮箱登录
    :param username_or_email: 用户名 或 邮箱
    :param password: 明文密码
    :return: 成功返回用户的 _id，失败返回 None
    """
    user = db.users.find_one({"$or": [{"username": username_or_email}, {"email": username_or_email}]})

    if user:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash == user["password_hash"]:
            return str(user["_id"])  # 返回用户 ID（字符串格式）

# 获取用户信息
def get_user_by_id(user_id):
    return db.users.find_one({"_id": ObjectId(user_id)})

# =============================== 仓库相关操作 ===============================

def create_repo(owner_id, repo_name, repo_desc):
    """
    创建一个repo并更新用户文档中的仓库列表
    输入检查: repo名不能与该用户所拥有的其他repo名字重复，并且owner_id必须是已经存在的
    :param owner_id 用户的 _id
    :param repo_name 当前的repo名
    :param repo_desc 对repo的描述

    :return: 出现任何错误都会只返回一个none，否则返回创建的 repo _id
    """
    # 检查用户是否存在
    owner = db.users.find_one({"_id": ObjectId(owner_id)})
    if not owner:
        return None  # 用户不存在，不能创建仓库

    # 检查仓库名是否重复（同一个用户下）
    existing_repo = db.repos.find_one({"owner_id": ObjectId(owner_id), "name": repo_name})
    if existing_repo:
        return None  # 同名仓库已经存在，不能创建

    # 创建仓库文档
    repo = {
        "name": repo_name,
        "owner_id": ObjectId(owner_id),
        "desc": repo_desc,
        "collaborators": [],
        "files": [],
        "results": []
    }
    # 将仓库插入到repos集合
    result = db.repos.insert_one(repo)
    repo_id = str(result.inserted_id)

    # 更新用户文档，添加新仓库的repo_id到repos列表
    db.users.update_one(
        {"_id": ObjectId(owner_id)},
        {"$push": {"repos": ObjectId(repo_id)}}
    )

    return repo_id


def update_repo_name(repo_id, new_name):
    """
    更新仓库名称
    :param repo_id: 要更新的仓库 _id
    :param new_name: 新仓库名称（不能与该用户的其他仓库同名）
    :return: 成功返回 "success"，失败返回 None
    """
    # 查找仓库
    repo = db.repos.find_one({"_id": ObjectId(repo_id)})
    if not repo:
        return None  # 仓库不存在

    owner_id = repo["owner_id"]  # 获取仓库所有者ID

    # 检查同一用户下是否已有相同名称的仓库
    existing_repo = db.repos.find_one({"owner_id": owner_id, "name": new_name})
    if existing_repo:
        return None  # 该用户已有同名仓库，不能重命名

    # 执行更新
    db.repos.update_one({"_id": ObjectId(repo_id)}, {"$set": {"name": new_name}})
    return "success"

def update_repo_desc(repo_id, new_desc):
    """
    更新仓库描述
    :param repo_id: 要更新的仓库 _id
    :param new_desc: 新的描述信息
    :return: 成功返回 "success"，失败返回 None
    """
    # 查找仓库是否存在
    repo = db.repos.find_one({"_id": ObjectId(repo_id)})
    if not repo:
        return None  # 仓库不存在

    # 执行更新
    db.repos.update_one({"_id": ObjectId(repo_id)}, {"$set": {"desc": new_desc}})
    return "success"

def get_repo_by_id(repo_id):
    """
    获得repo所有信息
    :param repo_id: 需要的仓库 _id
    :return: 返回仓库的整个数据结构
    """
    return db.repos.find_one({"_id": ObjectId(repo_id)})

def delete_repo(repo_id):
    """
    删除仓库，并更新相关用户的 repos 属性
    :param repo_id: 仓库的 ID
    :return: 成功删除返回 success
    """
    # 1. 删除仓库
    result = db.repos.delete_one({"_id": ObjectId(repo_id)})
    
    if result.deleted_count == 0:
        return "repo not found"
    
    # 2. 从所有用户的 repos 属性中删除该仓库 ID
    db.users.update_many(
        {"repos": ObjectId(repo_id)},
        {"$pull": {"repos": ObjectId(repo_id)}}
    )

    return "success"


def add_collaborator(repo_id, collaborator_id):
    """
    添加一个协作者
    :param repo_id 该仓库的_id(不能不存在)
    :param collaborator_id 协作者的_id(不能是该仓库的拥有者)
    :return: 成功添加则返回 success，否则返回none
    """
    # 检查仓库是否存在
    repo = db.repos.find_one({"_id": ObjectId(repo_id)})
    if not repo:
        print("仓库不存在")
        return None  # 仓库不存在，不能添加协作者

    # 检查协作者是否已经是该仓库的协作者
    if ObjectId(collaborator_id) in repo["collaborators"]:
        print("该用户已经是协作者")
        return None  # 协作者已经在列表中，无需重复添加

    # 添加协作者
    db.repos.update_one(
        {"_id": ObjectId(repo_id)},
        {"$addToSet": {"collaborators": ObjectId(collaborator_id)}}
    )

    # 添加协作仓库
    db.users.update_one(
        {"_id": ObjectId(collaborator_id)},
        {"$addToSet": {"collaborations": ObjectId(repo_id)}}
    )
    return "success"  # 成功添加协作者

# =============================== 文件相关操作 ===============================
def upload_res_file(repo_id: str, file_obj, source_file_id,filename: str, source=False):
    """
    上传结果文件到 GridFS，并更新 repo 的 files 或 results 列表
    :param repo_id: 仓库 ID
    :param file_obj: 需要上传的文件对象（二进制流）
    :param filename: 文件名
    :param source: 如果 source=True 则更新 files 列表，如果为 False 则更新 results 列表
    :return: 成功返回文件 ID，失败返回 None
    """
    repo = db.repos.find_one({"_id": ObjectId(repo_id)})
    if not repo:
        return None  # 仓库不存在

    file_content = file_obj.read()
    file_id = fs.put(file_content, filename=filename)
    file_size = len(file_content)


    file_info = {
        "source_file": ObjectId(source_file_id),
        "file_id": ObjectId(file_id),
        "filename": filename,
        "size": file_size,
        "uploaded_at": datetime.now(UTC),
        "status": "uploaded"
    }

    db.repos.update_one(
        {"_id": ObjectId(repo_id)},
        {"$push": {"files" if source else "results": file_info}}
    )

    return str(file_id)

def upload_source_file(repo_id: str, file_obj, filename: str, source=True):
    """
    上传文件到 GridFS，并更新 repo 的 files 或 results 列表
    :param repo_id: 仓库 ID
    :param file_obj: 需要上传的文件对象（二进制流）
    :param filename: 文件名
    :param source: 如果 source=True 则更新 files 列表，如果为 False 则更新 results 列表
    :return: 成功返回文件 ID，失败返回 None
    """
    repo = db.repos.find_one({"_id": ObjectId(repo_id)})
    if not repo:
        return None  # 仓库不存在

    file_content = file_obj.read()
    file_id = fs.put(file_content, filename=filename)
    file_size = len(file_content)


    file_info = {
        "source_file": False,
        "file_id": ObjectId(file_id),
        "filename": filename,
        "size": file_size,
        "uploaded_at": datetime.now(UTC),
        "status": "uploaded"
    }

    db.repos.update_one(
        {"_id": ObjectId(repo_id)},
        {"$push": {"files" if source else "results": file_info}}
    )

    return str(file_id)

def get_file_metadata_by_id(repo_id: str, file_id: str, source=True):
    """
    获取文件的元数据，包括 `status`
    :param repo_id: 仓库 ID
    :param file_id: 文件 ID
    :param source: 如果 source=True 则获得 files 信息，如果 False 则获得 results 信息
    :return: 文件元数据（字典格式），如果文件不存在则返回 None
    """
    repo_id_obj = ObjectId(repo_id)
    file_id_obj = ObjectId(file_id)

    collection_name = "files" if source else "results"

    repo = db.repos.find_one(
        {"_id": repo_id_obj, f"{collection_name}.file_id": file_id_obj},
        {f"{collection_name}.$": 1}
    )

    if not repo or collection_name not in repo or not repo[collection_name]:
        print(f"文件 {file_id} 不存在于 repo {repo_id}")
        return None

    file_data = repo[collection_name][0]

    return {
        "file_id": str(file_data["file_id"]),
        "filename": file_data["filename"],
        "size": file_data["size"],
        "upload_date": file_data["uploaded_at"],
        "status": str(file_data.get("status", "unknown"))
    }


def delete_file(file_id: str):
    """
    从 GridFS 删除文件，并从 repo.files 或 repo.results 中移除记录
    :param file_id: 文件的 `_id`
    :return: 成功返回 "success"，失败返回 None
    """
    file_id_obj = ObjectId(file_id)

    file_obj = db.fs.files.find_one({"_id": file_id_obj})
    if not file_obj:
        print(f"文件 {file_id} 不存在")
        return None

    fs.delete(file_id_obj)

    db.repos.update_many(
        {"files.file_id": file_id_obj},
        {"$pull": {"files": {"file_id": file_id_obj}}}
    )

    db.repos.update_many(
        {"results.file_id": file_id_obj},
        {"$pull": {"results": {"file_id": file_id_obj}}}
    )

    print(f"文件 {file_id} 删除成功")
    return "success"


def download_file(file_id: str):
    """
    从 GridFS 下载文件
    :param file_id: 文件的 `_id`
    :return: (文件名, 文件内容 bytes) 或 None
    """
    file_id_obj = ObjectId(file_id)
    file_obj = fs.get(file_id_obj)

    if not file_obj:
        print(f"文件 {file_id} 不存在")
        return None

    return file_obj.filename, file_obj.read()


def update_file_status(repo_id: str, file_id: str, new_status: str = "complete", source=True):
    """
    更新文件的 `status` 字段
    :param repo_id: 仓库 ID
    :param file_id: 文件 ID
    :param new_status: 要更新的状态（默认为 "complete"）
    :param source: 如果 source=True，则更新 files，否则更新 results
    :return: "success" 表示更新成功，"not found" 表示未找到文件
    """
    repo_id_obj = ObjectId(repo_id)
    file_id_obj = ObjectId(file_id)
    collection_name = "files" if source else "results"

    result = db.repos.update_one(
        {"_id": repo_id_obj, f"{collection_name}.file_id": file_id_obj},
        {"$set": {f"{collection_name}.$.status": new_status}}
    )

    if result.matched_count == 0:
        print(f"文件 {file_id} 不存在于 repo {repo_id}")
        return "not found"

    print(f"文件 {file_id} 状态更新为 {new_status}")
    return "success"


def create_or_get_chat_history(user_id: str, repo_id: str):
    """
    创建一个新的 chat_history，如果已存在则返回已有的 chat 记录。
    
    :param user_id: 用户的 id
    :param repo_id: 仓库的 id
    :return: 返回 chat 的 MongoDB _id（字符串格式），以及已有的 chat 记录
    """
    
    user_id_obj = ObjectId(user_id)
    repo_id_obj = ObjectId(repo_id)

    # 查询是否已有记录
    existing_chat = db.chats.find_one({"user_id": user_id_obj, "repo_id": repo_id_obj})
    if existing_chat:
        existing_chat["_id"] = str(existing_chat["_id"])  # 转换 ObjectId 为字符串
        return existing_chat  # 直接返回已有的 chat 记录
    
    # 创建新记录
    chat_history = {
        "user_id": user_id_obj,
        "repo_id": repo_id_obj,
        "texts": [],  # 初始化为空的聊天记录
    }
    result = db.chats.insert_one(chat_history)
    
    # 返回新插入的 chat 记录
    chat_history["_id"] = str(result.inserted_id)
    return chat_history

def update_chat_history(user_id: str, repo_id: str, question: Message, answer:Message):
    """
    往对应的 chat_history 里面新增一条 text 记录。
    
    :param user_id: 用户的 id
    :param repo_id: 仓库的 id
    :param text: 要添加的文本
    :return: 更新后的 chat 记录，如果失败则返回错误信息
    """
    user_id_obj = ObjectId(user_id)
    repo_id_obj = ObjectId(repo_id)
    # 查找 chat_history
    chat = db.chats.find_one({"user_id": user_id_obj, "repo_id": repo_id_obj})
    
    if not chat:
        return {"error": "Chat history not found."}
    question_dict = {
        "sayer": question.sayer,
        "text": question.text,
        "timestamp": question.timestamp.isoformat()
    }
    answer_dict = {
        "sayer": answer.sayer,
        "text": answer.text,
        "timestamp": answer.timestamp.isoformat()
    }
    # 更新 chat_history，追加新的 text
    text = {
        "question": str(question_dict),
        "answer": str(answer_dict)
    }
    db.chats.update_one(
        {"user_id": user_id_obj, "repo_id": repo_id_obj},
        {"$push": {"texts": text}}  # 追加文本
    )

    # 获取更新后的 chat_history 并返回
    updated_chat = db.chats.find_one({"user_id": user_id_obj, "repo_id": repo_id_obj})
    if updated_chat:
        updated_chat["_id"] = str(updated_chat["_id"])  # 转换 ObjectId 为字符串
    return updated_chat


def create_or_update_json_res(file_id: str, json_content):
    """
    创建一个json格式的结果
    :param file_id: 文件的id
    :param json_content: json格式的结果
    :return: 新生成的json_res的_id
    """
    file_id_obj = ObjectId(file_id)


    # 查询是否已有记录
    existing_json_res = db.json_res.find_one({"file_id": file_id_obj})

    if existing_json_res:
        db.json_res.update_one(
            {"file_id": file_id_obj},
            {"$set": {"content": json_content}}  
        )

        return str(existing_json_res["_id"])  # 转换 ObjectId 为字符串

    file_json = {
        "file_id": file_id_obj, 
        "content": json_content   
    }

    result = db.json_res.insert_one(file_json)
    return str(result.inserted_id)


def get_json_res(file_id: str):
    """
    返回json格式的结果
    :param file_id: 文件的id(注意这里是结果文件的id而不是json_res的id)
    :return: 对应的json_res，如果结果不存在则返回None
    """
    file_id_obj = ObjectId(file_id)
    json_res = db.json_res.find_one({"file_id": file_id_obj})
    if json_res:
        json_res["_id"] = str(json_res["_id"])  # 转换 ObjectId 为字符串
        return json_res  # 直接返回已有的 chat 记录
    return None



