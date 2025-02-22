from fastapi import APIRouter, HTTPException, Depends
from db.db_util import create_user, authenticate_user, get_user_by_id
from models.user import UserCreate, UserResponse, UserAuth, AuthResponse

router = APIRouter()

# 用户创建路由
@router.post("/", response_model=UserResponse)
async def create_new_user(user: UserCreate):
    """
    创建一个新的用户
    :param user:UserCreate
    :return: user id
    """
    user_id = create_user(user.username, user.email, user.password, user.profile_picture)
    cur_user = get_user_by_id(user_id)
    return objectID2str(cur_user)

# 用户认证路由
@router.post("/authenticate/", response_model=AuthResponse)
async def authenticate_user_request(user: UserAuth):
    """
    认证用户的登陆
    :param user:UserAuth
    :return: 如果成功，则返回AuthResponse，包含用户的user_id
             否则返回status_code:401
    """
    user_id = authenticate_user(user.username_or_email, user.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(user_id=user_id)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    通过user_id获得用户的信息
    :param user_id: 就是user的 _id
    :return: 如果成功，则返回user:UserResponse
             否则返回status_code:404
    """
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 将返回的 MongoDB 对象转换为 Pydantic 需要的格式
    return objectID2str(user)

def objectID2str(user):
    user_response = UserResponse(
        id=str(user["_id"]),  # 将 _id 转换为字符串
        username=user["username"],
        email=user["email"],
        profile_picture=user.get("profile_picture"),
        repos=[str(repo) for repo in user["repos"]],  # 将 repos 中的 ObjectId 转换为字符串
        collaborations=[str(collab) for collab in user["collaborations"]]
    )
    return user_response
    
