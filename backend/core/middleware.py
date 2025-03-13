"""
安全中间件模块

这个模块包含各种中间件，用于增强Web应用的安全性。

什么是中间件？
中间件是一种"中间人"组件，位于客户端请求和服务器响应之间。
每个请求在到达你的API端点之前，都会先经过所有的中间件处理。
同样，从API返回的响应在到达客户端之前，也会经过这些中间件。

中间件的作用：
1. 可以检查和修改进入的请求
2. 可以检查和修改外出的响应
3. 可以执行各种操作，如记录日志、添加安全头、限制请求速率等

这个模块中的中间件主要用于增强应用的安全性和可观测性。
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
    
    HTTP安全头是一种告诉浏览器如何处理网站内容的方式。
    正确设置这些头部可以防止多种常见的Web攻击，如：
    - XSS (跨站脚本攻击)：攻击者注入恶意脚本
    - 点击劫持：将你的网站嵌入在恶意网站的iframe中
    - MIME类型嗅探：浏览器猜测文件类型，可能导致安全问题
    - 等等
    """
    
    def __init__(self, app: ASGIApp):
        """
        初始化中间件
        
        这是中间件的构造函数，当应用启动时执行一次。
        
        参数:
            app: ASGI应用，这是FastAPI的底层应用对象
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并添加安全头
        
        这个方法会在每个请求被处理时调用。
        首先它让请求继续向下传递，然后修改返回的响应，添加各种安全头。
        
        参数:
            request: 客户端的HTTP请求
            call_next: 下一个处理函数，调用它来获取响应
            
        返回:
            Response: 添加了安全头的HTTP响应
        """
        # 调用下一个中间件或应用处理函数，获取响应
        response = await call_next(request)
        
        # 添加各种安全头
        # X-XSS-Protection: 启用浏览器内置的XSS过滤器
        # 值为"1; mode=block"表示检测到XSS攻击时阻止整个页面加载
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # X-Content-Type-Options: 防止浏览器猜测文件类型
        # "nosniff"值告诉浏览器严格按照响应的Content-Type处理内容
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: 控制页面是否可以被嵌入到iframe中
        # "DENY"表示完全禁止在iframe中加载，防止点击劫持攻击
        response.headers["X-Frame-Options"] = "DENY"
        
        # Strict-Transport-Security: 强制使用HTTPS连接
        # 告诉浏览器在指定时间内(31536000秒=1年)只使用HTTPS访问
        # includeSubDomains表示此规则也适用于所有子域名
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content-Security-Policy: 内容安全策略，精细控制页面可以加载的资源
        # 这是防御XSS最强大的方法之一
        # 下面的策略允许从同一域名加载大多数资源，但有一些例外
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval';"
        
        # Referrer-Policy: 控制浏览器发送Referer头的行为
        # strict-origin-when-cross-origin仅在跨域且安全性相同或更高时发送来源信息
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: 控制网页可以使用哪些浏览器功能
        # 这里的设置禁止网页使用摄像头、麦克风和地理位置
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    实现请求速率限制的中间件
    
    详细说明:
    这个中间件通过限制来自同一IP的请求频率来防止过度使用API。
    它使用简单的内存存储来跟踪每个IP地址的请求次数，并在超过
    限制时拒绝请求。这有助于防止DoS攻击和API滥用。
    
    工作原理:
    1. 为每个IP地址维护一个请求计数器和时间戳
    2. 每当收到新请求时，检查是否超过限制
    3. 如果超过限制，返回429错误(太多请求)
    4. 定期清理过期的请求记录以节省内存
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        rate_limit: int = 100, 
        time_window: int = 60,
        exclude_paths: List[str] = None
    ):
        """
        初始化速率限制中间件
        
        参数:
            app: ASGI应用对象
            rate_limit: 时间窗口内允许的最大请求数
            time_window: 时间窗口大小(秒)
            exclude_paths: 不受速率限制的路径列表(正则表达式)
        """
        super().__init__(app)
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.exclude_paths = exclude_paths or []
        self.ip_requests = {}  # 存储每个IP的请求信息
        self.last_cleanup = time.time()  # 上次清理过期数据的时间
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并实施速率限制
        
        详细说明:
        每个请求进入时，检查客户端IP是否已超过速率限制。
        如果请求路径在排除列表中，则不应用限制。
        如果客户端请求过于频繁，返回429状态码。
        
        参数:
            request: 客户端的HTTP请求
            call_next: 下一个处理函数
            
        返回:
            Response: HTTP响应或错误响应
        """
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # 检查路径是否在排除列表中
        for exclude_pattern in self.exclude_paths:
            if re.match(exclude_pattern, path):
                return await call_next(request)
        
        # 获取当前时间
        current_time = time.time()
        
        # 定期清理过期数据(每小时一次)
        if current_time - self.last_cleanup > 3600:
            self._cleanup_expired_data(current_time)
            self.last_cleanup = current_time
        
        # 检查IP是否已存在于记录中
        if client_ip in self.ip_requests:
            requests_info = self.ip_requests[client_ip]
            # 清除过期记录
            requests_info["timestamps"] = [
                ts for ts in requests_info["timestamps"] if current_time - ts < self.time_window
            ]
            
            # 检查是否超过速率限制
            if len(requests_info["timestamps"]) >= self.rate_limit:
                return Response(
                    content="Rate limit exceeded. Please try again later.",
                    status_code=429,
                    headers={"Retry-After": str(self.time_window)}
                )
            
            # 添加新请求时间戳
            requests_info["timestamps"].append(current_time)
        else:
            # 为新IP创建记录
            self.ip_requests[client_ip] = {
                "timestamps": [current_time]
            }
        
        # 处理请求
        return await call_next(request)
    
    def _cleanup_expired_data(self, current_time: float):
        """
        清理过期的IP请求数据
        
        详细说明:
        移除所有过期的IP请求记录，以防止内存无限增长。
        如果IP的所有请求时间戳都已过期，则完全移除该IP记录。
        
        参数:
            current_time: 当前时间戳
        """
        # 创建要删除的IP列表
        ips_to_delete = []
        
        # 检查每个IP
        for ip, requests_info in self.ip_requests.items():
            # 过滤出未过期的时间戳
            valid_timestamps = [
                ts for ts in requests_info["timestamps"] 
                if current_time - ts < self.time_window
            ]
            
            # 如果没有有效时间戳，标记IP待删除
            if not valid_timestamps:
                ips_to_delete.append(ip)
            else:
                # 更新有效时间戳
                requests_info["timestamps"] = valid_timestamps
        
        # 删除标记的IP
        for ip in ips_to_delete:
            del self.ip_requests[ip]

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志记录中间件
    
    详细说明:
    这个中间件记录每个HTTP请求和响应的关键信息，
    包括响应时间、状态码、路径和方法。
    这对于监控API使用情况、性能问题和调试非常有用。
    
    记录内容:
    - HTTP方法 (GET, POST, PUT等)
    - 请求路径
    - 响应状态码
    - 处理时间(毫秒)
    - 客户端IP地址
    - 用户代理(浏览器信息)
    """
    
    def __init__(self, app: ASGIApp):
        """
        初始化日志中间件
        
        参数:
            app: ASGI应用对象
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录日志
        
        详细说明:
        记录请求开始时间，处理请求，然后记录结束时间和其他详细信息。
        所有信息以结构化格式打印到控制台，可以轻松集成到日志系统中。
        
        参数:
            request: 客户端的HTTP请求
            call_next: 下一个处理函数
            
        返回:
            Response: 原始的HTTP响应
        """
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间(毫秒)
        process_time = (time.time() - start_time) * 1000
        
        # 获取响应状态码
        status_code = response.status_code
        
        # 记录请求和响应信息
        log_msg = (
            f"Method: {method} | "
            f"Path: {path} | "
            f"Status: {status_code} | "
            f"Time: {process_time:.2f}ms | "
            f"IP: {client_ip} | "
            f"User-Agent: {user_agent}"
        )
        
        # 根据状态码决定日志级别
        if status_code >= 500:
            print(f"ERROR - {log_msg}")  # 服务器错误
        elif status_code >= 400:
            print(f"WARNING - {log_msg}")  # 客户端错误
        else:
            print(f"INFO - {log_msg}")  # 正常响应
        
        return response

class CORSMiddleware(BaseHTTPMiddleware):
    """
    跨域资源共享(CORS)中间件
    
    详细说明:
    这个中间件处理跨域资源共享(CORS)策略，允许来自指定域的
    前端应用安全地与API通信。CORS是一种浏览器安全机制，要求
    服务器明确声明哪些源可以访问其资源。
    
    作用:
    - 添加必要的CORS头部，如Access-Control-Allow-Origin
    - 处理预检(OPTIONS)请求
    - 控制允许的HTTP方法和头部
    - 决定是否允许发送凭据(如cookies)
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = False,
        max_age: int = 600  # 10分钟
    ):
        """
        初始化CORS中间件
        
        参数:
            app: ASGI应用对象
            allow_origins: 允许访问的源列表(域名)
            allow_methods: 允许的HTTP方法
            allow_headers: 允许的HTTP头部
            allow_credentials: 是否允许包含凭据(cookies等)
            max_age: 预检请求结果缓存时间(秒)
        """
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并添加CORS头部
        
        详细说明:
        对于每个请求，添加适当的CORS头部。
        对于OPTIONS预检请求，直接返回带有CORS头部的响应，无需进一步处理。
        对于普通请求，将CORS头部添加到正常响应中。
        
        参数:
            request: 客户端的HTTP请求
            call_next: 下一个处理函数
            
        返回:
            Response: 带有CORS头部的HTTP响应
        """
        # 获取Origin头部
        origin = request.headers.get("origin")
        
        # 如果请求没有Origin头，或者不允许任何源，则不添加CORS头
        if not origin:
            return await call_next(request)
        
        # 检查是否允许该源
        allow_origin = "*"
        if self.allow_origins != ["*"]:
            allow_origin = origin if origin in self.allow_origins else ""
        
        # 如果不允许该源，处理请求但不添加CORS头
        if not allow_origin:
            return await call_next(request)
        
        # 准备CORS头部
        headers = {
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
            "Access-Control-Max-Age": str(self.max_age)
        }
        
        # 如果允许凭据，添加对应头部
        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        # 处理预检请求
        if request.method == "OPTIONS":
            return Response(
                content="",
                status_code=200,
                headers=headers
            )
        
        # 处理实际请求
        response = await call_next(request)
        
        # 添加CORS头部到响应
        for key, value in headers.items():
            response.headers[key] = value
        
        return response

def add_middleware(app: FastAPI):
    """
    添加所有中间件到应用
    
    详细说明:
    这个函数将所有定义的中间件添加到FastAPI应用中。
    中间件按照反向顺序调用，即最后添加的中间件最先处理请求。
    因此，添加顺序很重要。
    
    中间件顺序说明:
    1. CORSMiddleware - 首先处理，因为如果跨域检查失败，后续处理没有意义
    2. SecurityHeadersMiddleware - 添加安全头部
    3. RateLimitMiddleware - 速率限制检查
    4. RequestLoggingMiddleware - 最后记录完整的请求处理过程
    
    参数:
        app: FastAPI应用实例
    """
    # 添加CORS中间件(处理跨域资源共享)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有源，生产环境应设置为特定域名
        allow_methods=["*"],  # 允许所有HTTP方法
        allow_headers=["*"],  # 允许所有请求头
        allow_credentials=True  # 允许包含凭证(如cookies)
    )
    
    # 添加安全头部中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 添加请求速率限制中间件
    app.add_middleware(
        RateLimitMiddleware,
        rate_limit=100,  # 每分钟100个请求
        time_window=60,  # 60秒窗口
        exclude_paths=[
            r"^/docs",  # 排除Swagger文档
            r"^/redoc",  # 排除Redoc文档
            r"^/openapi.json"  # 排除OpenAPI定义
        ]
    )
    
    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware) 