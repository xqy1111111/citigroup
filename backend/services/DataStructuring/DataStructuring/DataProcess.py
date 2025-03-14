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

# 线程本地存储
thread_local = threading.local()

# 文件类型集合
AllowTypeSet={"PDF","DOCX","DOC","XLS","XLSX","PPT","PPTX","PNG","JPG","JPEG","CSV","PY","TXT","MD","BMP","GIF",
              "pdf","docx","doc","xls","xlsx","ppt","pptx","png","jpg","jpeg","csv","py","txt","md","bmp","gif"}
AudioTypeSet={"MP3","M4A","WAV", "mp3","m4a","wav"}
VideoTypeSet={"MP4","AVI","MPEG","MPG","MPE", "mp4","avi","mpeg","mpg","mpe"}

# 获取线程安全的日志记录器
def get_thread_logger():
    """
    获取线程安全的日志记录器
    
    功能：
    - 为每个线程创建独立的日志记录器，避免冲突
    - 记录线程和进程ID，便于调试
    
    返回：
        logger: 配置好的日志记录器
    """
    if not hasattr(thread_local, 'logger'):
        process_id = os.getpid()
        thread_id = threading.get_ident()
        logger_name = f"DataProcess-{process_id}-{thread_id}"
        
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

def ProcessData(SourcePath, TextPath, max_workers=None):
    """
    该函数会处理SourceData下面的文件，将所有格式文件转换成文本文件
    
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
    
    # 遍历所有文件
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
    if max_workers is None:
        import multiprocessing
        # 使用CPU核心数的2倍，但最多20个线程，最少2个线程
        max_workers = min(max(2, multiprocessing.cpu_count() * 2), 20, total_files)
    
    logger.info(f"使用 {max_workers} 个线程并行处理文件")
    
    # 创建结果队列，用于收集处理结果
    result_queue = queue.Queue()
    
    # 创建线程池并行处理文件
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(process_single_file, str(filepath), TextPath, result_queue): filepath
            for filepath in files_to_process
        }
        
        # 处理结果
        completed = 0
        for future in concurrent.futures.as_completed(future_to_file):
            filepath = future_to_file[future]
            try:
                result = future.result()
                if result:
                    completed += 1
                # 每处理5个文件或达到总数时打印进度
                if completed % 5 == 0 or completed == total_files:
                    logger.info(f"已处理 {completed}/{total_files} 文件 ({completed*100/total_files:.1f}%)")
            except Exception as e:
                logger.error(f"处理文件 {filepath} 时出错: {str(e)}")
    
    # 收集处理结果统计
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
    logger = get_thread_logger()
    try:
        # 识别文件类型
        file_type = FileTypeRecognize(filepath)
        
        # 如果无法识别文件类型
        if file_type is None:
            logger.warning(f"无法识别文件类型: {filepath}")
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
        file_name = os.path.basename(filepath)
        text_file_name = pattern_substitute(file_name, ".txt")
        text_file_path = os.path.join(TextPath, text_file_name)
        
        # 写入文本内容
        write_to_txt_os(text_file_path, content)
        
        # 记录成功结果
        result_queue.put({"success": True, "path": filepath, "output": text_file_path})
        return True
        
    except Exception as e:
        # 记录错误
        logger.error(f"处理文件异常: {filepath}: {str(e)}")
        result_queue.put({"success": False, "reason": "exception", "error": str(e), "path": filepath})
        return False