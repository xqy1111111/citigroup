from fastapi import FastAPI
from api.user import router as user_router
from api.repo import router as repo_router
from api.auth import router as auth_router  # 导入认证路由
from api._file import router as file_router
from api.chat import router as chat_router
from api.process import router as process_router
from fastapi.middleware.cors import CORSMiddleware
from core.middleware import add_security_middlewares  # 导入安全中间件函数

# 创建 FastAPI 实例
app = FastAPI(
    title="My FastAPI Project",
    description="安全的后端API服务",
    version="1.0.0",
    # 添加联系信息和许可证信息
    contact={
        "name": "开发团队",
        "email": "dev@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# 配置CORS
# 在生产环境中，应将origins替换为实际的前端域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 将通配符替换为特定的前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明确列出允许的HTTP方法，而不是使用通配符
    allow_headers=["Authorization", "Content-Type", "Accept"],  # 明确列出允许的HTTP请求头，而不是使用通配符
)

# 添加安全中间件
add_security_middlewares(app)

# 注册 API 路由
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])  # 注册认证路由
app.include_router(repo_router, prefix="/repos", tags=["Repos"])
app.include_router(file_router, prefix="/files", tags=["Files"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(process_router, prefix="/process", tags=["Process"])

@app.get("/", tags=["Health"])
async def root():
    """
    健康检查端点
    
    返回:
        dict: 包含API状态信息的字典
    """
    return {"status": "healthy", "api_version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
