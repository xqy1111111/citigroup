"""
日志中间件模块

此模块提供FastAPI中间件组件，实现：
1. 请求追踪 - 为每个请求生成唯一ID
2. 访问日志 - 记录请求和响应信息
3. 性能监控 - 记录请求处理时间

请求追踪功能使得在分布式系统中可以追踪单个请求的完整流程，
帮助调试和性能分析。
"""
import time
import uuid
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# 使用Loguru替代标准logging
from loguru import logger
import structlog

# 导入设置trace_id的函数
from .log_config import set_trace_id

# 获取structlog记录器，用于结构化日志
struct_logger = structlog.get_logger("access")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    为每个HTTP请求生成唯一的trace_id，并记录请求/响应信息
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        处理请求并记录日志
        
        参数:
            request: 客户端请求
            call_next: 下一个要调用的中间件或路由处理函数
            
        返回:
            Response: 响应对象
        """
        # 生成请求的唯一ID
        trace_id = self._generate_trace_id()
        
        # 设置trace_id到日志系统
        set_trace_id(trace_id)
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        await self._log_request(request, trace_id)
        
        try:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)
            
            # 添加trace_id到响应头
            response.headers["X-Trace-ID"] = trace_id
            
            # 计算请求处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            self._log_response(request, response, process_time, trace_id)
            
            return response
        except Exception as e:
            # 记录异常并返回500响应
            process_time = time.time() - start_time
            logger.exception(
                f"请求处理异常: {str(e)}", 
                trace_id=trace_id, 
                logger_type="access",
                url=str(request.url),
                method=request.method,
                process_time_ms=round(process_time * 1000, 2)
            )
            
            # 创建错误响应
            from fastapi.responses import JSONResponse
            error_response = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error", "trace_id": trace_id}
            )
            
            # 添加trace_id到错误响应头
            error_response.headers["X-Trace-ID"] = trace_id
            
            return error_response
        
    def _generate_trace_id(self) -> str:
        """
        生成唯一的请求追踪ID
        
        返回:
            str: UUID格式的追踪ID
        """
        return str(uuid.uuid4())
        
    async def _log_request(self, request: Request, trace_id: str):
        """
        记录请求信息
        
        参数:
            request: FastAPI请求对象
            trace_id: 请求追踪ID
        """
        # 获取客户端IP
        client_host = request.client.host if request.client else "unknown"
        
        # 尝试获取请求体内容（仅记录小型请求体）
        body = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # 备份请求体指针
                body_position = await request.body()
                await request.json()
                # 恢复请求体指针，避免影响后续处理
                request._body = body_position
                body = "JSON数据，已接收"
            except:
                body = "非JSON数据或无法解析"
                
        # 构建请求日志信息
        log_data = {
            "event": "http_request",
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_host,
            "headers": dict(request.headers),
            "body_summary": body
        }
        
        # 使用loguru记录请求日志
        logger.info(
            f"收到请求: {json.dumps(log_data)}", 
            trace_id=trace_id, 
            logger_type="access"
        )
        
        # 使用structlog记录结构化日志
        struct_logger.info(
            "收到请求",
            trace_id=trace_id,
            **log_data
        )
            
    def _log_response(self, request: Request, response: Response, process_time: float, trace_id: str):
        """
        记录响应信息
        
        参数:
            request: 客户端请求
            response: 服务器响应
            process_time: 请求处理时间(秒)
            trace_id: 请求追踪ID
        """
        # 构建响应日志信息
        log_data = {
            "event": "http_response",
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),  # 转换为毫秒
            "response_headers": dict(response.headers)
        }
        
        # 根据状态码选择日志级别
        if 200 <= response.status_code < 400:
            # 成功响应
            logger.info(
                f"请求成功: {json.dumps(log_data)}", 
                trace_id=trace_id, 
                logger_type="access"
            )
            struct_logger.info("请求成功", trace_id=trace_id, **log_data)
        elif 400 <= response.status_code < 500:
            # 客户端错误
            logger.warning(
                f"客户端错误: {json.dumps(log_data)}", 
                trace_id=trace_id, 
                logger_type="access"
            )
            struct_logger.warning("客户端错误", trace_id=trace_id, **log_data)
        else:
            # 服务器错误
            logger.error(
                f"服务器错误: {json.dumps(log_data)}", 
                trace_id=trace_id, 
                logger_type="access"
            )
            struct_logger.error("服务器错误", trace_id=trace_id, **log_data)

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    关联ID中间件
    
    允许客户端提供自己的追踪ID，或者在没有提供时生成一个新的
    这对于微服务架构很有用，可以跨多个服务追踪请求
    """
    def __init__(self, app: ASGIApp, header_name: str = "X-Correlation-ID"):
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 尝试从请求头获取关联ID
        correlation_id = request.headers.get(self.header_name)
        
        # 如果没有关联ID，则生成一个新的
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # 设置为trace_id
        set_trace_id(correlation_id)
        
        # 使用loguru记录调试信息
        logger.debug(
            f"关联ID: {correlation_id}", 
            correlation_id=correlation_id, 
            logger_type="access"
        )
        
        # 调用下一个中间件或处理函数
        response = await call_next(request)
        
        # 添加关联ID到响应头
        response.headers[self.header_name] = correlation_id
        
        return response 