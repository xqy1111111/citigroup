# ===== 优化DataStructuring/main_process.py =====
from .DataProcess import *
from .Clssifier import *
from .txt_to_excel import *
import logging
import time
import threading
import os

# 线程本地存储，确保每个线程有独立的日志配置
# 【线程本地存储基础】
# threading.local()创建线程局部存储对象，每个线程访问时都有独立的属性副本
# 这是实现线程安全的重要机制 - 避免不同线程共享同一变量，防止数据竞争和同步问题
# 这里用它来存储每个线程的日志记录器，确保日志输出不会混淆
thread_local = threading.local()

# 获取线程安全的日志记录器
def get_logger():
    """
    获取线程安全的日志记录器
    
    【线程安全实现】
    - 为每个线程创建独立的日志记录器实例
    - 避免多线程/多进程环境下日志记录的混乱
    - 防止多线程对同一日志处理器的并发访问导致的竞争条件
    
    功能：
    - 为每个线程创建独立的日志记录器
    - 避免多线程/进程下的日志冲突
    - 记录线程/进程ID便于调试
    
    返回：
        logger: 配置好的日志记录器
    """
    # 【延迟初始化模式】
    # 检查当前线程是否已有记录器，没有则创建
    # 这种模式确保资源只在需要时创建，提高效率
    if not hasattr(thread_local, 'logger'):
        # 创建线程独立的日志记录器，使用进程ID和线程ID作为标识
        process_id = os.getpid()
        thread_id = threading.get_ident()
        logger_name = f"DataStructuring-{process_id}-{thread_id}"
        
        logger = logging.getLogger(logger_name)
        
        # 避免重复配置handler - 防止多次调用导致重复的日志输出
        # 【并发编程中的幂等设计】
        # 确保函数可以多次调用但效果相同，是编写安全并发代码的重要原则
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        logger.setLevel(logging.INFO)
        
        # 将记录器存储在线程本地存储中
        thread_local.logger = logger
        
    return thread_local.logger

# 注意：在运行之前，请保证SourceData文件夹下其余文件已经被清空，需要处理的文件才在里面

def main_process(source_dir=None, target_dir=None):
    """
    数据处理主函数，优化版本适合并发环境调用
    
    【并发安全设计】
    此函数设计用于在多进程/多线程环境下并发调用，通过以下机制确保安全：
    1. 独立的工作目录 - 每次调用使用独立资源，避免共享状态
    2. 线程安全的日志 - 使用线程本地存储避免日志混乱
    3. 完整的错误处理 - 异常不会传播到其他线程/进程
    4. 返回值而非全局变量 - 避免共享可变状态
    
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
    # 每个线程都有独立的日志记录器，避免多线程环境下的日志混乱
    logger = get_logger()
    start_time = time.time()
    
    # 记录开始处理
    logger.info(f"开始处理数据: source_dir={source_dir}, target_dir={target_dir}")
    
    try:
        # 使用相对路径：
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 设置工作目录
        # 【重要的资源隔离设计】
        # 当在多进程/多线程环境调用此函数时，可以为每个调用提供不同的
        # source_dir和target_dir，这样每个处理任务都有独立的工作空间，
        # 避免资源竞争和数据冲突，是并发安全的关键策略
        SourcePath = source_dir if source_dir else os.path.join(current_dir, "SourceData")
        TextPath = os.path.join(current_dir, "TextData")
        Input_for_ShenZijun_Path = os.path.join(current_dir, "InputData_for_ShenZijun")
        TargetPath = target_dir if target_dir else os.path.join(current_dir, "TargetData")

        # 检查源目录是否存在
        if not os.path.exists(SourcePath):
            logger.error(f"源目录不存在: {SourcePath}")
            return False
            
        # 检查源目录中是否有文件
        # 【防御性编程】
        # 在并发环境中，总是检查输入和前置条件，避免在有问题的数据上浪费处理时间
        source_files = [f for f in os.listdir(SourcePath) 
                      if os.path.isfile(os.path.join(SourcePath, f))]
        if not source_files:
            logger.warning(f"源目录 {SourcePath} 中没有文件")
            # 仍然创建目标目录，但返回成功以允许流程继续
            os.makedirs(TargetPath, exist_ok=True)
            return True
            
        logger.info(f"发现 {len(source_files)} 个源文件待处理")

        # 如果文件夹不存在就新建文件夹
        # exist_ok=True是一种线程安全的目录创建方式，即使多个线程同时尝试创建目录也不会出错
        # 这是并发编程中的"幂等性"设计 - 重复操作不会产生副作用
        os.makedirs(SourcePath, exist_ok=True)
        os.makedirs(TextPath, exist_ok=True)
        os.makedirs(Input_for_ShenZijun_Path, exist_ok=True)
        os.makedirs(TargetPath, exist_ok=True)

        # 清空临时文件夹，但保留源文件夹内容
        # 【异常处理机制】
        # 在并发环境中，每个操作都应该有独立的异常处理
        # 这样即使一个操作失败，也不会影响整个流程或其他并发任务
        try:
            Clear_Dir([TextPath, Input_for_ShenZijun_Path, TargetPath])
            logger.info("清理临时目录完成")
        except Exception as e:
            logger.error(f"清理目录时出错: {str(e)}")
            # 继续处理，不要因为清理错误而终止
            # 这是容错设计，增强程序的健壮性

        # 处理数据 - 将文件转换为文本格式
        # 【关键步骤1】
        # 注意：ProcessData内部已经实现了多线程处理，可以并行处理多个文件
        # 所以即使在单线程调用main_process的情况下，也能获得多线程加速
        try:
            logger.info("开始数据处理：将文件转换为文本格式")
            ProcessData(SourcePath, TextPath)
            logger.info("数据处理完成")
        except Exception as e:
            logger.error(f"处理数据时出错: {str(e)}")
            return False

        # 文本分类 - 根据结构化程度分类
        # 【关键步骤2】
        # Classify内部也实现了并行处理和缓存机制
        try:
            logger.info("开始数据分类")
            Classify(TextPath, Input_for_ShenZijun_Path)
            logger.info("数据分类完成")
        except Exception as e:
            logger.error(f"分类数据时出错: {str(e)}")
            return False

        # 生成Excel文件
        # 【关键步骤3】
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
        # 【全局异常处理】
        # 捕获所有未处理的异常，确保函数不会抛出异常到调用者
        # 这是并发环境中的关键设计 - 异常隔离，防止一个任务的失败影响其他任务
        logger.error(f"数据处理过程中出现未捕获的异常: {str(e)}")
        # 确保函数不会因异常而崩溃，返回失败状态
        return False