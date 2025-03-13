"""
用户API路由模块

这个模块实现了与用户相关的所有API端点，包括：
1. 用户注册 - 创建新用户
2. 用户认证 - 验证用户凭据
3. 用户信息获取 - 查询用户详情

这些API构成了用户管理的基础功能，使前端应用能够进行用户注册、登录和个人资料显示。
"""
from fastapi import APIRouter, HTTPException, Depends
from db.db_util import create_user, authenticate_user, get_user_by_id
from models.user import UserCreate, UserResponse, UserAuth, AuthResponse

# 创建路由器实例
# APIRouter是FastAPI提供的一种组织端点的方式，可以将相关端点组合在一起
router = APIRouter()

# 用户创建路由
@router.post("/", response_model=UserResponse)
async def create_new_user(user: UserCreate):
    """
    创建新用户API
    
    详细说明:
    这个端点接收用户注册信息，创建新用户，并返回创建的用户信息。
    整个流程包括:
    1. 接收并验证用户提交的注册数据(通过UserCreate模型)
    2. 调用数据库函数创建用户
    3. 获取并返回创建后的用户详情
    
    参数:
        user: UserCreate - 包含用户注册信息的请求体，包括用户名、邮箱、密码等
        
    返回:
        UserResponse - 用户创建成功后的详细信息，不包含敏感数据如密码
        
    错误:
        可能由数据库函数抛出错误，如用户名已存在等
    """
    # 调用数据库工具函数创建用户
    user_id = create_user(user.username, user.email, user.password, user.profile_picture)
    
    # 获取创建后的用户信息
    cur_user = get_user_by_id(user_id)
    
    # 将MongoDB文档转换为API响应格式并返回
    return objectID2str(cur_user)

# 用户认证路由
@router.post("/authenticate/", response_model=AuthResponse)
async def authenticate_user_request(user: UserAuth):
    """
    用户登录认证API
    
    详细说明:
    这个端点处理用户登录请求，验证用户凭据(用户名/邮箱和密码)。
    认证成功返回用户ID，失败则返回401错误。
    
    认证流程:
    1. 接收用户名/邮箱和密码
    2. 调用数据库函数验证凭据
    3. 成功则返回用户ID，失败则返回错误
    
    参数:
        user: UserAuth - 包含登录凭据的请求体，包括用户名/邮箱和密码
        
    返回:
        AuthResponse - 包含用户ID的认证响应
        
    错误:
        401 Unauthorized - 如果用户凭据无效
    """
    # 调用数据库工具函数验证用户凭据
    user_id = authenticate_user(user.username_or_email, user.password)
    
    # 如果认证失败，抛出401未授权错误
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 认证成功，返回用户ID
    return AuthResponse(user_id=user_id)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    获取用户信息API
    
    详细说明:
    这个端点根据用户ID查询并返回用户的详细信息。
    通常用于获取用户个人资料或用户详情页面。
    
    流程:
    1. 接收用户ID参数
    2. 调用数据库函数查询用户
    3. 将数据库文档转换为API响应格式
    
    参数:
        user_id: str - 用户的唯一标识符
        
    返回:
        UserResponse - 用户的详细信息
        
    错误:
        404 Not Found - 如果指定ID的用户不存在
    """
    # 调用数据库工具函数获取用户信息
    user = get_user_by_id(user_id)
    
    # 如果用户不存在，抛出404错误
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 将MongoDB文档转换为API响应格式并返回
    return objectID2str(user)

def objectID2str(user):
    """
    工具函数：将MongoDB文档转换为API响应格式
    
    详细说明:
    MongoDB使用ObjectId类型作为文档ID，但在JSON响应中需要使用字符串。
    这个函数将MongoDB用户文档转换为符合UserResponse模型的格式。
    
    转换内容:
    1. 将MongoDB的_id转换为字符串ID
    2. 将repos和collaborations列表中的ObjectId转换为字符串
    3. 按照UserResponse模型的结构组织数据
    
    参数:
        user: dict - MongoDB用户文档
        
    返回:
        UserResponse - 符合API响应格式的用户数据
    """
    # 创建符合UserResponse模型的对象
    user_response = UserResponse(
        id=str(user["_id"]),  # 将MongoDB的_id转换为字符串
        username=user["username"],
        email=user["email"],
        profile_picture=user.get("profile_picture"),  # 使用get避免字段不存在时出错
        repos=[str(repo) for repo in user["repos"]],  # 将仓库ID列表中的ObjectId转换为字符串
        collaborations=[str(collab) for collab in user["collaborations"]]  # 将协作仓库ID列表转换为字符串
    )
    return user_response
    
