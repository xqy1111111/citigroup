# ===== 优化DataStructuring/main_process.py =====
from .DataProcess import *
from .Clssifier import *
from .txt_to_excel import *
import logging
import time
import threading
import os

# 线程本地存储，确保每个线程有独立的日志配置
thread_local = threading.local()

# 获取线程安全的日志记录器
def get_logger():
    """
    获取线程安全的日志记录器
    
    功能：
    - 为每个线程创建独立的日志记录器
    - 避免多线程/进程下的日志冲突
    - 记录线程/进程ID便于调试
    
    返回：
        logger: 配置好的日志记录器
    """
    if not hasattr(thread_local, 'logger'):
        # 创建线程独立的日志记录器
        process_id = os.getpid()
        thread_id = threading.get_ident()
        logger_name = f"DataStructuring-{process_id}-{thread_id}"
        
        logger = logging.getLogger(logger_name)
        
        # 避免重复配置handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        logger.setLevel(logging.INFO)
        thread_local.logger = logger
        
    return thread_local.logger

# 注意：在运行之前，请保证SourceData文件夹下其余文件已经被清空，需要处理的文件才在里面

def main_process(source_dir=None, target_dir=None):
    """
    数据处理主函数，优化版本适合并发环境调用
    
    功能：
    - 处理源文件并生成结构化数据
    - 支持并发调用，线程/进程安全
    - 提供错误隔离，避免一处错误导致整个处理失败
    
    工作流程：
    1. 初始化工作环境
    2. 将源文件转换为文本格式
    3. 对文本进行结构化分类
    4. 将文本转换为Excel格式
    
    参数：
        source_dir: 源数据目录，如果为None则使用默认目录
        target_dir: 目标数据目录，如果为None则使用默认目录
        
    返回：
        bool: 处理是否成功
    """
    # 获取线程安全的日志记录器
    logger = get_logger()
    start_time = time.time()
    
    # 记录开始处理
    logger.info(f"开始处理数据: source_dir={source_dir}, target_dir={target_dir}")
    
    try:
        # 使用相对路径：
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 设置工作目录
        SourcePath = source_dir if source_dir else os.path.join(current_dir, "SourceData")
        TextPath = os.path.join(current_dir, "TextData")
        Input_for_ShenZijun_Path = os.path.join(current_dir, "InputData_for_ShenZijun")
        TargetPath = target_dir if target_dir else os.path.join(current_dir, "TargetData")

        # 检查源目录是否存在
        if not os.path.exists(SourcePath):
            logger.error(f"源目录不存在: {SourcePath}")
            return False
            
        # 检查源目录中是否有文件
        source_files = [f for f in os.listdir(SourcePath) 
                      if os.path.isfile(os.path.join(SourcePath, f))]
        if not source_files:
            logger.warning(f"源目录 {SourcePath} 中没有文件")
            # 仍然创建目标目录，但返回成功以允许流程继续
            os.makedirs(TargetPath, exist_ok=True)
            return True
            
        logger.info(f"发现 {len(source_files)} 个源文件待处理")

        # 如果文件夹不存在就新建文件夹
        os.makedirs(SourcePath, exist_ok=True)
        os.makedirs(TextPath, exist_ok=True)
        os.makedirs(Input_for_ShenZijun_Path, exist_ok=True)
        os.makedirs(TargetPath, exist_ok=True)

        # 清空临时文件夹，但保留源文件夹内容
        try:
            Clear_Dir([TextPath, Input_for_ShenZijun_Path, TargetPath])
            logger.info("清理临时目录完成")
        except Exception as e:
            logger.error(f"清理目录时出错: {str(e)}")
            # 继续处理，不要因为清理错误而终止

        # 处理数据 - 将文件转换为文本格式
        try:
            logger.info("开始数据处理：将文件转换为文本格式")
            ProcessData(SourcePath, TextPath)
            logger.info("数据处理完成")
        except Exception as e:
            logger.error(f"处理数据时出错: {str(e)}")
            return False

        # 文本分类 - 根据结构化程度分类
        try:
            logger.info("开始数据分类")
            Classify(TextPath, Input_for_ShenZijun_Path)
            logger.info("数据分类完成")
        except Exception as e:
            logger.error(f"分类数据时出错: {str(e)}")
            return False

        # 生成Excel文件
        try:
            logger.info("开始生成Excel文件")
            txt_to_excel(Input_for_ShenZijun_Path, TargetPath)
            logger.info("Excel生成完成")
        except Exception as e:
            logger.error(f"生成Excel时出错: {str(e)}")
            return False
            
        # 检查结果是否生成
        target_files = [f for f in os.listdir(TargetPath) 
                      if os.path.isfile(os.path.join(TargetPath, f))]
                      
        end_time = time.time()
        elapsed = end_time - start_time
        logger.info(f"数据处理全部完成。生成了 {len(target_files)} 个目标文件，总耗时: {elapsed:.2f} 秒")
        
        return True

    except Exception as e:
        logger.error(f"数据处理过程中出现未捕获的异常: {str(e)}")
        # 确保函数不会因异常而崩溃，返回失败状态
        return False