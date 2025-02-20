from fastapi import APIRouter
from .endpoints import users, repos, files, chat

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(repos.router, prefix="/repos", tags=["repos"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"]) 