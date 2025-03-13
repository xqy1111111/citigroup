"""
安全中间件模块
包含用于增强应用安全性的各种中间件
"""
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Callable, List
import re

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    为响应添加安全HTTP头的中间件
    
    安全头的设置对于防止各种常见的Web攻击（如XSS、点击劫持等）至关重要
    """
    
    def __init__(self, app: ASGIApp):
        """
        初始化中间件
        
        参数:
            app: ASGI应用
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并添加安全头
        
        参数:
            request: 客户端请求
            call_next: 下一个中间件或应用处理函数
            
        返回:
            Response: 带有安全头的响应
        """
        # 调用下一个中间件或应用处理函数
        response = await call_next(request)
        
        # 添加安全头
        # X-XSS-Protection: 启用浏览器的XSS过滤器
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # X-Content-Type-Options: 防止浏览器进行MIME类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: 防止页面被嵌入到iframe中，防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"
        
        # Strict-Transport-Security: 强制使用HTTPS连接
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content-Security-Policy: 控制页面可以加载的资源
        # 这里设置一个基础策略，实际应用中应根据需求定制
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval';"
        
        # Referrer-Policy: 控制Referer头的发送方式
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: 控制浏览器功能和API的使用
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    实现简单的基于内存的请求速率限制中间件
    
    注意：在生产环境中，应使用Redis等分布式缓存来实现速率限制
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        rate_limit: int = 60,  # 默认每分钟60个请求
        time_window: int = 60,  # 默认时间窗口为60秒
        exclude_paths: List[str] = None  # 排除的路径列表
    ):
        """
        初始化中间件
        
        参数:
            app: ASGI应用
            rate_limit: 在时间窗口内允许的最大请求数
            time_window: 时间窗口大小，单位为秒
            exclude_paths: 排除在速率限制之外的路径列表
        """
        super().__init__(app)
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.exclude_paths = exclude_paths or []
        # 用于存储客户端请求记录的字典
        # 格式：{client_ip: [(timestamp1), (timestamp2), ...]}
        self.client_requests = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并实施速率限制
        
        参数:
            request: 客户端请求
            call_next: 下一个中间件或应用处理函数
            
        返回:
            Response: 响应对象，如果超过速率限制则返回429错误
        """
        # 检查是否为排除路径
        for path in self.exclude_paths:
            if re.match(path, request.url.path):
                return await call_next(request)
        
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 初始化或清理客户端请求记录
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []
        else:
            # 移除时间窗口外的请求记录
            self.client_requests[client_ip] = [
                timestamp for timestamp in self.client_requests[client_ip]
                if current_time - timestamp <= self.time_window
            ]
        
        # 检查是否超过速率限制
        if len(self.client_requests[client_ip]) >= self.rate_limit:
            # 返回429 Too Many Requests响应
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later."
                },
                headers={
                    "Retry-After": str(self.time_window)  # 建议客户端等待的时间
                }
            )
        
        # 记录当前请求的时间戳
        self.client_requests[client_ip].append(current_time)
        
        # 处理请求
        return await call_next(request)

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    记录请求和响应信息的中间件
    
    用于审计和调试目的，记录请求的方法、路径、状态码和处理时间
    """
    
    def __init__(self, app: ASGIApp):
        """
        初始化中间件
        
        参数:
            app: ASGI应用
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录信息
        
        参数:
            request: 客户端请求
            call_next: 下一个中间件或应用处理函数
            
        返回:
            Response: 响应对象
        """
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        # 在实际应用中，应使用合适的日志库（如logging）而不是print
        client_ip = request.client.host if request.client else "unknown"
        request_id = request.headers.get("X-Request-ID", "")
        print(f"[{request_id}] Request: {request.method} {request.url.path} from {client_ip}")
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录响应信息
        # 同样，在实际应用中应使用日志库
        print(f"[{request_id}] Response: {response.status_code} in {process_time:.3f}s")
        
        # 在响应头中添加处理时间，便于客户端调试
        # 在生产环境中可以考虑移除这个头部
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response

def add_security_middlewares(app: FastAPI) -> None:
    """
    向FastAPI应用添加安全中间件
    
    参数:
        app: FastAPI应用实例
    """
    # 添加安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 添加速率限制中间件
    # 排除静态文件和文档路径
    app.add_middleware(
        RateLimitMiddleware,
        rate_limit=100,  # 每分钟100个请求
        time_window=60,  # 1分钟时间窗口
        exclude_paths=[r"/docs.*", r"/openapi.json", r"/static/.*"]
    )
    
    # 添加请求日志中间件
    app.add_middleware(RequestLoggerMiddleware) 