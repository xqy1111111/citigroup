"""
FastAPI主应用程序入口

这个文件是整个后端项目的入口点，它完成以下工作：
1. 创建FastAPI应用实例
2. 配置CORS(跨域资源共享)以允许前端访问
3. 添加各种安全中间件
4. 注册所有API路由
5. 提供健康检查端点
6. 配置日志系统和请求追踪功能

理解这个文件对于掌握整个项目结构至关重要
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from api.user import router as user_router
from api.repo import router as repo_router
from api.auth import router as auth_router  # 导入认证路由
from api._file import router as file_router
from api.chat import router as chat_router
from api.process import router as process_router
from api.websocket import handle_websocket
from fastapi.middleware.cors import CORSMiddleware
from core.middleware import add_middleware  # 导入安全中间件函数
from starlette.websockets import WebSocketState

# 导入日志系统 - 使用增强版的Loguru和structlog
from core.logging import setup_logging, logger, get_logger
import logging
import os

# 确定环境类型（开发、测试、生产）
# 在生产环境中，通常会通过环境变量设置
ENV = os.getenv("APP_ENV", "development")

# 创建 FastAPI 实例
# 这里定义了API的基本信息，如标题、描述和版本号，这些信息会显示在自动生成的API文档中
app = FastAPI(
    title="My FastAPI Project",
    description="安全的后端API服务",
    version="1.0.0",
    # 添加联系信息和许可证信息，这些都会出现在API文档页面上
    contact={
        "name": "开发团队",
        "email": "dev@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# 配置日志系统
# 根据环境设置不同的日志级别和格式
if ENV == "production":
    # 生产环境使用JSON格式，便于日志聚合和分析
    root_logger = setup_logging(app, level="INFO", enable_json=True)
    logger.info(f"应用启动于生产环境", environment="production")
    
    # 生产环境中使用结构化日志
    struct_logger = get_logger("app")
    struct_logger.info("应用启动", environment="production", version="1.0.0")
elif ENV == "testing":
    # 测试环境
    root_logger = setup_logging(app, level="DEBUG")
    logger.info(f"应用启动于测试环境", environment="testing")
else:
    # 开发环境使用INFO级别的日志，减少不必要的调试信息
    root_logger = setup_logging(app, level="INFO")
    logger.info(f"应用启动于开发环境", environment="development")

# 配置CORS(跨域资源共享)中间件
# CORS是一种安全机制，控制哪些外部网站可以访问你的API
# 默认情况下，浏览器禁止网页向不同源的服务器发送请求，这就是"同源策略"
# 通过CORS，我们可以安全地放宽这一限制
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，或者使用特定域名列表
    allow_credentials=True,  # 允许发送凭证（如cookies）
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 添加安全中间件
# 安全中间件可以帮助防止各种常见的Web攻击，如XSS、CSRF、注入攻击等
add_middleware(app)

# 注册 API 路由
# 这里将各个模块的路由注册到主应用中，并设置URL前缀和标签
# 例如，所有用户相关的API都以/users开头，并在文档中归类为"Users"标签
app.include_router(user_router, prefix="/users", tags=["Users"])  # 用户管理相关API
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])  # 认证相关API
app.include_router(repo_router, prefix="/repos", tags=["Repos"])  # 仓库管理相关API
app.include_router(file_router, prefix="/files", tags=["Files"])  # 文件处理相关API
app.include_router(chat_router, prefix="/chat", tags=["Chat"])  # 聊天功能相关API
app.include_router(process_router, prefix="/process", tags=["Process"])  # 处理流程相关API

@app.get("/", tags=["Health"])
async def root(request: Request):
    """
    健康检查端点
    
    这个端点主要用于监控系统，可以用来检查API服务是否正常运行。
    当你调用这个端点时，如果返回预期的响应，说明API服务器正常工作。
    这对于部署和维护非常重要，可以结合监控工具使用。
    
    返回:
        dict: 包含API状态信息的字典，包括状态标识和版本号
    """
    # 记录健康检查日志 - 使用结构化字段
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"健康检查请求",
        client_ip=client_ip,
        endpoint="health",
        request_path=request.url.path
    )
    
    return {
        "status": "healthy", 
        "api_version": "1.0.0",
        "environment": ENV
    }

@app.websocket("/ws/{repo_id}")
async def websocket_endpoint(websocket: WebSocket, repo_id: str):
    token = websocket.query_params.get("token")
    try:
        await handle_websocket(websocket, repo_id, token)
    except WebSocketDisconnect:
        print(f"WebSocket连接断开: {repo_id}")
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1000)

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    
    捕获所有未处理的异常，进行日志记录并返回统一的错误响应
    """
    # 从请求上下文获取trace_id
    trace_id = request.headers.get("X-Trace-ID", "unknown")
    
    # 记录异常详情 - 使用结构化字段，便于后续分析
    logger.exception(
        f"未捕获的异常: {str(exc)}",
        trace_id=trace_id,
        url=str(request.url),
        method=request.method,
        client_ip=request.client.host if request.client else "unknown",
        exception_type=type(exc).__name__
    )
    
    # 使用structlog记录可机器处理的结构化日志
    struct_logger = get_logger("error")
    struct_logger.error(
        "未捕获的异常",
        trace_id=trace_id,
        url=str(request.url),
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__
    )
    
    # 返回友好的错误信息
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "trace_id": trace_id  # 返回trace_id便于问题追踪
        }
    )

if __name__ == "__main__":
    # 当直接运行此文件时，启动开发服务器
    # 在生产环境中，通常会使用gunicorn或uvicorn的命令行启动
    import uvicorn
    
    # 配置uvicorn日志
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(message)s",  # 简化的日志格式
            },
        },
        "handlers": {
            "default": {
                "formatter": "simple",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }
    
    # 启动服务器，使用自定义日志配置
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,  # reload=True启用热重载，代码修改后自动重启服务器
        log_config=log_config
    )
