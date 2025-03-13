"""
日志系统配置模块

此模块提供了一个全面的日志系统配置，使用Loguru和structlog实现：
1. 控制台日志输出 - 便于开发调试，使用rich美化显示
2. 文件日志输出 - 用于持久化存储日志记录
3. 日志轮转功能 - 自动管理日志文件大小和数量
4. 不同级别的日志处理 - 区分不同严重程度的信息
5. 结构化日志 - 支持JSON格式，便于分析和处理

日志级别说明：
- DEBUG: 详细的调试信息，用于开发和调试
- INFO: 一般操作信息，确认程序按预期工作
- WARNING: 表示可能出现问题的警告，但程序仍在工作
- ERROR: 由于更严重的问题，程序部分功能无法执行
- CRITICAL: 严重错误，程序可能无法继续运行

这个配置可以根据不同环境(开发、测试、生产)进行调整
"""
import os
import sys
import uuid
import json
import logging
from pathlib import Path
from typing import Dict, Any

# 导入新的日志库
from loguru import logger
import structlog
from rich.console import Console
from rich.logging import RichHandler
from python_json_logger import JsonLogger

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 日志存储目录
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件路径
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, 'app.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error.log')
ACCESS_LOG_FILE = os.path.join(LOG_DIR, 'access.log')

# 默认的trace_id
DEFAULT_TRACE_ID = "no-trace-id"

# 当前上下文的trace_id (全局变量)
TRACE_ID = DEFAULT_TRACE_ID

# 配置Rich处理器用于美化控制台输出
rich_console = Console(width=100, color_system="auto")
rich_handler = RichHandler(console=rich_console, rich_tracebacks=True)

def add_trace_id_to_record(_, __, event_dict):
    """为structlog添加trace_id到日志记录"""
    global TRACE_ID
    event_dict["trace_id"] = TRACE_ID
    return event_dict

def configure_structlog():
    """配置structlog用于结构化日志记录"""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            add_trace_id_to_record,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    )
    return structlog.get_logger()

# 兼容标准logging的处理类，用于与现有代码平滑过渡
class LoguruHandler(logging.Handler):
    """将标准logging日志转发到loguru"""
    def emit(self, record):
        # 从记录中提取trace_id，如果没有则使用默认值
        trace_id = getattr(record, 'trace_id', TRACE_ID)
        
        # 根据日志级别调用相应的loguru方法
        level = logger.level(record.levelname).name
        
        # 准备额外的上下文信息
        extras = {
            "trace_id": trace_id,
            "logger_name": record.name,
            "path": record.pathname,
            "line": record.lineno
        }
        
        # 构造消息并添加异常信息
        message = self.format(record)
        logger.bind(**extras).log(level, message)

def setup_standard_logging():
    """配置标准logging库与loguru的兼容"""
    # 移除所有现有的处理器
    logging.root.handlers.clear()
    
    # 添加转发到loguru的处理器
    handler = LoguruHandler()
    logging.root.addHandler(handler)
    
    # 默认级别设为DEBUG，让loguru决定是否记录
    logging.root.setLevel(logging.DEBUG)

def configure_logging(level="INFO", enable_json=False):
    """
    配置日志系统
    
    参数:
        level: 日志级别，默认为INFO
        enable_json (bool): 是否启用JSON格式日志，用于生产环境
        
    这个函数会配置整个应用的日志系统，包括:
    1. loguru配置 - 主要的日志记录系统
    2. structlog配置 - 用于结构化日志
    3. 标准logging兼容性 - 支持已有代码平滑过渡
    """
    # 移除所有默认处理器
    logger.remove()
    
    # 添加控制台处理器，使用Rich美化
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> | <yellow>trace_id={extra[trace_id]}</yellow> | <level>{message}</level>"
    
    logger.add(
        rich_handler,
        format=log_format,
        level=level,
        colorize=True
    )
    
    # 添加文件处理器 - 主日志文件
    file_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | trace_id={extra[trace_id]} | {message}"
    json_format = lambda record: json.dumps({
        "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S"),
        "level": record["level"].name,
        "message": record["message"],
        "name": record["name"],
        "line": record["line"],
        "trace_id": record["extra"].get("trace_id", DEFAULT_TRACE_ID),
        "exception": record["exception"]
    })
    
    logger.add(
        DEFAULT_LOG_FILE,
        format=json_format if enable_json else file_format,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",   # 压缩旧日志
        level=level,
        enqueue=True  # 异步写入
    )
    
    # 添加错误日志文件 - 仅ERROR和CRITICAL级别
    logger.add(
        ERROR_LOG_FILE,
        format=json_format if enable_json else file_format,
        rotation="10 MB",  # 每10MB轮转
        retention=10,  # 保留10个备份
        compression="zip",
        level="ERROR",
        enqueue=True
    )
    
    # 添加访问日志文件 - 通过过滤器区分
    logger.add(
        ACCESS_LOG_FILE,
        format=json_format if enable_json else file_format,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",
        compression="zip",
        filter=lambda record: record["extra"].get("logger_type") == "access",
        level="INFO",
        enqueue=True
    )
    
    # 配置structlog
    struct_logger = configure_structlog()
    
    # 设置标准logging库与loguru的兼容
    setup_standard_logging()
    
    # 创建并返回根日志记录器 (兼容原有API)
    root_logger = logging.getLogger()
    
    # 记录初始化完成日志
    logger.info("日志系统已配置完成", trace_id=DEFAULT_TRACE_ID)
    
    return root_logger

def set_trace_id(trace_id):
    """
    为当前上下文设置trace_id
    
    这个函数可以在请求处理开始时调用，设置当前请求的唯一标识符
    """
    global TRACE_ID
    TRACE_ID = trace_id

# 提供与原始日志系统兼容的类和函数，方便代码过渡
class TraceIDFilter:
    """
    兼容原有TraceIDFilter的API
    """
    def __init__(self, name="", trace_id=DEFAULT_TRACE_ID):
        set_trace_id(trace_id)
        self.trace_id = trace_id
        
    def filter(self, record):
        if not hasattr(record, 'trace_id'):
            record.trace_id = self.trace_id
        return True

class JsonFormatter:
    """
    兼容原有JsonFormatter的API
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record) if hasattr(self, 'formatTime') else record.created,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger_name": record.name,
            "path": record.pathname,
            "line": record.lineno,
            "trace_id": getattr(record, 'trace_id', DEFAULT_TRACE_ID)
        }
        
        # 添加异常信息（如果有）
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info) if hasattr(self, 'formatException') else str(record.exc_info)
            
        return json.dumps(log_record)

if __name__ == "__main__":
    # 测试日志配置
    configure_logging(level="DEBUG")
    test_logger = logging.getLogger(__name__)
    
    # 设置trace_id
    set_trace_id("test-trace-123")
    
    # 测试不同级别的日志记录
    test_logger.debug("这是一条调试信息")
    test_logger.info("这是一条信息")
    test_logger.warning("这是一条警告")
    test_logger.error("这是一条错误信息")
    
    # 测试异常日志
    try:
        1/0
    except Exception as e:
        test_logger.exception("发生了除零错误")
        
    # 测试loguru直接记录
    logger.debug("Loguru调试信息", trace_id="test-trace-123")
    logger.info("Loguru信息", trace_id="test-trace-123")
    
    # 测试structlog
    struct_logger = structlog.get_logger()
    struct_logger.info("结构化日志测试") 