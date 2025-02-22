from fastapi import FastAPI
from api.user import router as user_router
from api.repo import router as repo_router
from api._file import router as file_router
from api.chat import router as chat_router
from api.process import router as process_router

# 创建 FastAPI 实例
app = FastAPI(title="My FastAPI Project")

# 注册 API 路由
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(repo_router, prefix="/repos", tags=["Repos"])
app.include_router(file_router, prefix="/files", tags=["Files"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(process_router, prefix="/process", tags=["Process"])
