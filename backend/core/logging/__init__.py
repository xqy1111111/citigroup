"""
日志系统包初始化

此模块导出日志系统的核心功能，简化导入和使用。
同时提供了一个便捷的setup_logging函数，用于在应用启动时配置日志系统。

使用Loguru和structlog实现高级日志功能，包括：
- 结构化日志记录
- 美化的控制台输出
- 自动日志轮转
- 异常跟踪
- 请求追踪
"""
# 导入标准库模块
import logging

# 导入Loguru和structlog
from loguru import logger
import structlog

# 导入配置
from .log_config import (
    configure_logging, 
    set_trace_id, 
    TraceIDFilter, 
    JsonFormatter,
    DEFAULT_TRACE_ID
)

# 导入中间件
from .middleware import RequestLoggingMiddleware, CorrelationIDMiddleware

# 导出所有关键组件
__all__ = [
    'configure_logging',
    'set_trace_id',
    'TraceIDFilter',
    'JsonFormatter',
    'RequestLoggingMiddleware',
    'CorrelationIDMiddleware',
    'setup_logging',
    'DEFAULT_TRACE_ID',
    'logger',  # 导出loguru实例，方便直接使用
    'get_logger'  # 导出获取structlog记录器的函数
]

def get_logger(name=None):
    """
    获取结构化日志记录器
    
    参数:
        name: 记录器名称，默认为None（使用调用模块名）
        
    返回:
        structlog记录器实例
    """
    return structlog.get_logger(name)

def setup_logging(app=None, level="INFO", enable_json=False):
    """
    设置应用的日志系统
    
    参数:
        app: FastAPI应用实例，如果提供则添加日志中间件
        level: 日志级别，可以是字符串或logging模块的常量
        enable_json: 是否启用JSON格式日志输出
        
    这是一个便捷函数，集成了日志配置和中间件添加功能，
    适合在应用启动时调用。
    """
    # 将字符串级别转换为logging模块常量
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'无效的日志级别: {level}')
        level = numeric_level
    
    # 配置日志系统
    configure_logging(level=level, enable_json=enable_json)
    
    # 如果提供了app，添加中间件
    if app:
        # 添加关联ID中间件
        app.add_middleware(CorrelationIDMiddleware)
        # 添加请求日志中间件
        app.add_middleware(RequestLoggingMiddleware)
    
    # 记录初始化信息
    logger.info("日志系统已设置，Loguru和structlog已启用", setup="complete")
        
    # 返回根记录器
    return logging.getLogger()  # 返回根日志记录器，保持与原来API兼容 