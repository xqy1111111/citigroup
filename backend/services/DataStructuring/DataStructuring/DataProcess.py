# ===== 优化DataStructuring/DataProcess.py =====
from .GeneralProcess import *
from .ParticularProcess import *
from .MyFunctions import *
import filetype
import os
import re
import threading
import queue
import logging
import concurrent.futures
from pathlib import Path
import time

# ===== 文件类型定义 =====
# 支持处理的文件类型集合
AllowTypeSet={"PDF","DOCX","DOC","XLS","XLSX","PPT","PPTX","PNG","JPG","JPEG","CSV","PY","TXT","MD","BMP","GIF",
              "pdf","docx","doc","xls","xlsx","ppt","pptx","png","jpg","jpeg","csv","py","txt","md","bmp","gif"}
AudioTypeSet={"MP3","M4A","WAV", "mp3","m4a","wav"}
VideoTypeSet={"MP4","AVI","MPEG","MPG","MPE", "mp4","avi","mpeg","mpg","mpe"}

# ===== 线程安全机制 =====
# 【线程本地存储】
# 创建线程局部存储对象，用于在多线程环境中为每个线程维护独立的数据副本
# 这是线程安全编程的重要机制，避免线程间共享数据导致的竞争条件和同步问题
thread_local = threading.local()

# 获取线程安全的日志记录器
def get_thread_logger():
    """
    获取线程安全的日志记录器
    
    【并发安全设计】
    - 每个线程使用独立的日志记录器，避免并发写入冲突
    - 线程ID作为日志名称的一部分，便于跟踪不同线程的日志
    - 延迟初始化模式，只在实际需要时创建资源
    
    功能：
    - 为每个线程创建独立的日志记录器，避免冲突
    - 记录线程和进程ID，便于调试
    
    返回：
        logger: 配置好的日志记录器
    """
    # 检查当前线程是否已有日志记录器，这是线程安全的延迟初始化模式
    if not hasattr(thread_local, 'logger'):
        # 使用进程ID和线程ID创建唯一标识的日志记录器名称
        process_id = os.getpid()
        thread_id = threading.get_ident()
        logger_name = f"DataProcess-{process_id}-{thread_id}"
        
        logger = logging.getLogger(logger_name)
        
        # 避免重复配置handler - 防止重复调用导致的日志重复
        # 这是实现幂等操作的一种方式，确保相同操作多次执行效果相同
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        logger.setLevel(logging.INFO)
        thread_local.logger = logger
        
    return thread_local.logger

def ProcessData(SourcePath, TextPath, max_workers=None):
    """
    该函数会处理SourceData下面的文件，将所有格式文件转换成文本文件
    
    【多线程并行处理】
    此函数实现了多线程并行处理文件的能力，通过以下机制提高性能：
    1. 线程池 - 高效管理多个工作线程，避免频繁创建销毁线程的开销
    2. 动态线程数 - 根据CPU核心数和任务特性自动调整最佳线程数
    3. 结果队列 - 使用线程安全的队列收集处理结果，避免竞争条件
    4. 并发执行 - 将文件处理任务分配给多个线程并行执行
    
    优化点：
    - 添加并发处理能力
    - 智能决定最佳线程数
    - 增强错误处理和日志
    - 提供处理进度反馈
    
    参数：
        SourcePath: 源文件目录
        TextPath: 目标文本目录
        max_workers: 最大工作线程数，None表示自动决定
    """
    # 获取线程安全的日志记录器
    logger = get_thread_logger()
    start_time = time.time()
    
    # 确保给定的路径存在且是一个目录
    if not CheckDirExist(SourcePath) or not CheckDirExist(TextPath):
        logger.error(f"目录不存在: {SourcePath} 或 {TextPath}")
        return False
        
    # 收集所有需要处理的文件
    logger.info(f"开始扫描源目录: {SourcePath}")
    files_to_process = []
    path = Path(SourcePath)
    
    # 遍历所有文件并收集路径
    # 在多线程处理前，先创建完整的任务列表
    for filepath in path.rglob('*'):
        if not filepath.is_file():
            continue
        files_to_process.append(filepath)
    
    # 统计找到的文件数量
    total_files = len(files_to_process)
    logger.info(f"发现 {total_files} 个文件需要处理")
    
    if total_files == 0:
        logger.warning("没有找到需要处理的文件")
        return True
    
    # 确定最佳线程数
    # 【线程池大小优化】
    # 线程池大小是并发性能的关键因素：
    # - 线程太少：无法充分利用CPU
    # - 线程太多：上下文切换开销大，反而降低性能
    # 通常对于I/O密集型任务，可以使用较多线程（CPU核心数的2-4倍）
    # 对于CPU密集型任务，线程数接近CPU核心数较为合适
    if max_workers is None:
        import multiprocessing
        # 使用CPU核心数的2倍，但最多20个线程，最少2个线程
        # 这是经验法则：I/O密集型任务适合使用更多线程
        max_workers = min(max(2, multiprocessing.cpu_count() * 2), 20, total_files)
    
    logger.info(f"使用 {max_workers} 个线程并行处理文件")
    
    # 创建结果队列，用于收集处理结果
    # 【线程安全的队列】
    # Queue是线程安全的数据结构，多个线程可以安全地向其中添加或获取元素
    # 不需要额外的锁机制，适合在并发环境中收集结果
    result_queue = queue.Queue()
    
    # 创建线程池并行处理文件
    # 【线程池并发执行】
    # ThreadPoolExecutor是Python标准库提供的线程池实现，相比手动创建线程有几个优势：
    # 1. 自动管理线程生命周期，避免手动创建销毁线程的开销
    # 2. 提供工作队列，自动调度任务执行
    # 3. 提供Future接口，简化结果收集和异常处理
    # 4. with语句确保线程池使用后自动关闭，防止资源泄漏
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        # 【映射任务到线程池】
        # 使用字典将Future对象与对应的文件路径关联起来
        # 这样在处理结果时可以知道每个结果对应的是哪个文件
        future_to_file = {
            executor.submit(process_single_file, str(filepath), TextPath, result_queue): filepath
            for filepath in files_to_process
        }
        
        # 处理结果
        # 【处理完成的任务】
        # as_completed返回已完成的Future对象迭代器，按完成顺序而非提交顺序
        # 这样可以处理最先完成的任务，而不必等待它们按顺序完成
        completed = 0
        for future in concurrent.futures.as_completed(future_to_file):
            filepath = future_to_file[future]
            try:
                # 获取任务结果，如果执行过程中有异常，future.result()会重新引发该异常
                result = future.result()
                if result:
                    completed += 1
                # 每处理5个文件或达到总数时打印进度
                # 这减少了日志输出频率，避免日志太多影响性能
                if completed % 5 == 0 or completed == total_files:
                    logger.info(f"已处理 {completed}/{total_files} 文件 ({completed*100/total_files:.1f}%)")
            except Exception as e:
                logger.error(f"处理文件 {filepath} 时出错: {str(e)}")
    
    # 收集处理结果统计
    # 【结果聚合】
    # 处理完所有任务后，从结果队列中收集统计信息
    # 这个过程是在所有线程完成后在主线程中执行的，不需要线程同步机制
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    while not result_queue.empty():
        result = result_queue.get()
        if result.get("success", False):
            success_count += 1
        elif result.get("skipped", False):
            skipped_count += 1
        else:
            error_count += 1
    
    # 计算处理时间
    end_time = time.time()
    elapsed = end_time - start_time
    
    # 输出最终统计
    logger.info(f"文件处理完成。成功: {success_count}, 跳过: {skipped_count}, 失败: {error_count}, 总耗时: {elapsed:.2f} 秒")
    
    # 只要有文件成功处理，就返回成功
    return success_count > 0

def process_single_file(filepath, TextPath, result_queue):
    """
    处理单个文件，并将结果放入队列
    
    【工作线程函数】
    此函数在线程池的工作线程中执行，设计时考虑了以下并发安全因素：
    1. 线程安全的日志 - 使用线程本地存储的日志记录器
    2. 无共享状态 - 函数不依赖或修改全局状态
    3. 结果隔离 - 使用队列传递结果，避免直接返回
    4. 异常处理 - 捕获并记录异常，不会影响其他线程
    
    功能：
    - 识别文件类型
    - 调用相应的处理函数
    - 生成文本文件
    - 记录处理结果
    
    参数：
        filepath: 源文件路径
        TextPath: 目标文本目录
        result_queue: 结果队列，用于收集处理统计
    
    返回：
        bool: 处理是否成功
    """
    # 获取线程安全的日志记录器
    # 在每个工作线程中都获取独立的日志记录器
    logger = get_thread_logger()
    try:
        # 识别文件类型
        file_type = FileTypeRecognize(filepath)
        
        # 如果无法识别文件类型
        if file_type is None:
            logger.warning(f"无法识别文件类型: {filepath}")
            # 将结果放入队列，而不是直接返回
            # 这是线程池编程的典型模式 - 使用队列传递结果
            result_queue.put({"skipped": True, "reason": "unknown_type", "path": filepath})
            return False
            
        # 根据文件类型选择处理方法
        content = None
        if file_type in AllowTypeSet:
            logger.debug(f"处理普通文件: {filepath} (类型: {file_type})")
            content = GeneralFile(filepath=filepath)
        elif file_type in AudioTypeSet:
            logger.debug(f"处理音频文件: {filepath} (类型: {file_type})")
            content = AudioFile(filepath=filepath, type=file_type)
        else:
            logger.info(f"不支持处理的文件类型 {file_type}: {filepath}")
            result_queue.put({"skipped": True, "reason": "unsupported_type", "path": filepath})
            return False
            
        # 检查是否成功提取内容
        if not content:
            logger.warning(f"无法提取内容: {filepath}")
            result_queue.put({"success": False, "reason": "empty_content", "path": filepath})
            return False
            
        # 创建文本文件名并写入内容
        # 【文件安全处理】
        # 注意：在多线程环境中，必须确保每个线程写入不同的文件
        # 这里使用文件名作为唯一标识，避免多线程写入冲突
        file_name = os.path.basename(filepath)
        text_file_name = pattern_substitute(file_name, ".txt")
        text_file_path = os.path.join(TextPath, text_file_name)
        
        # 写入文本内容
        # 【文件I/O操作】
        # 在多线程环境中，文件I/O操作通常是线程安全的
        # 只要不同线程操作不同的文件，就不会发生冲突
        write_to_txt_os(text_file_path, content)
        
        # 记录成功结果
        # Queue.put是线程安全的操作，多个线程可以同时调用
        result_queue.put({"success": True, "path": filepath, "output": text_file_path})
        return True
        
    except Exception as e:
        # 记录错误
        # 【异常隔离】
        # 捕获并记录所有异常，防止异常传播导致整个线程池崩溃
        # 这是多线程编程中的重要原则 - 线程中的异常应该在线程内处理
        logger.error(f"处理文件异常: {filepath}: {str(e)}")
        result_queue.put({"success": False, "reason": "exception", "error": str(e), "path": filepath})
        return False