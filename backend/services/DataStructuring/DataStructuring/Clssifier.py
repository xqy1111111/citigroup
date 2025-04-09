from .GeneralProcess import *
from .MyFunctions import *
import logging
import threading
import time
import functools
import os
import concurrent.futures
from pathlib import Path

# 定义结构化级别常量
StructureLevels = ["结构化数据", "半结构化数据", "非结构化数据"]

# 线程本地存储
thread_local = threading.local()

# 为避免重复调用API，使用缓存装饰器
def lru_cache_with_timeout(maxsize=128, timeout=3600):
    """
    带超时的LRU缓存装饰器
    
    功能：
    - 缓存API调用结果，减少重复请求
    - 设置超时时间，定期更新缓存
    - 线程安全的缓存实现
    
    参数：
        maxsize: 最大缓存项数
        timeout: 缓存超时时间（秒）
    """
    def wrapper_cache(func):
        # 创建标准的LRU缓存
        func = functools.lru_cache(maxsize=maxsize)(func)
        # 保存最后访问时间
        func.lifetime = {}
        func.cache_lock = threading.RLock()
        
        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):
            # 检查缓存是否超时
            now = time.time()
            with func.cache_lock:
                # 检查键是否在缓存中
                key = functools._make_key(args, kwargs, typed=False)
                if key in func.lifetime and now - func.lifetime[key] > timeout:
                    # 超时，删除缓存项
                    func.cache_info()  # 必须先调用，刷新内部状态
                    func.cache_clear()
                    func.lifetime.clear()
                
                # 调用函数并更新访问时间
                result = func(*args, **kwargs)
                func.lifetime[key] = now
                return result
                
        return wrapped_func
    return wrapper_cache

# 获取线程安全的日志记录器
def get_logger():
    """
    获取线程安全的日志记录器
    
    功能：
    - 为每个线程创建独立的日志记录器
    - 避免多线程环境下的日志冲突
    - 记录线程ID便于调试
    
    返回：
        logger: 配置好的日志记录器
    """
    if not hasattr(thread_local, 'logger'):
        process_id = os.getpid()
        thread_id = threading.get_ident()
        logger_name = f"Classifier-{process_id}-{thread_id}"
        
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

# 缓存的模型查询函数
@lru_cache_with_timeout(maxsize=1000, timeout=1800)  # 缓存1000条记录，超时30分钟
def cached_query_model(content_hash, content):
    """
    带缓存的模型查询函数
    
    功能：
    - 使用哈希值作为键缓存查询结果
    - 减少对大语言模型的重复调用
    - 提高分类效率，降低API成本
    
    参数：
        content_hash: 内容哈希值，用于缓存
        content: 待分类的文本内容
        
    返回：
        str: 分类结果
    """
    logger = get_logger()
    
    try:
        # 调用大语言模型API接口
        logger.info(f"调用模型API分类文本 (hash: {content_hash})")
        
        # 使用GLM-4或其他模型进行分类
        response = client.chat.completions.create(
            model="glm-4-flash",  # 使用的模型名称
            messages=[
                {"role": "user",
                 "content": f"""请分析以下文本内容，并判断它是属于哪一类数据：
                1. 结构化数据：如表格、数据库记录等，有明确的字段和值
                2. 半结构化数据：如JSON、XML等，有一定结构但不如表格严格
                3. 非结构化数据：如自然语言文本、图像等
                
                请只回答"结构化数据"、"半结构化数据"或"非结构化数据"，不要解释原因。
                
                文本内容：
                {content}
                """}
            ],
            max_tokens=20,  # 限制输出长度，节省token
            temperature=0  # 使用确定性输出，避免随机性
        )
        
        # 获取模型回答
        answer = response.choices[0].message.content
        
        # 确保结果是预期的三个级别之一
        for level in StructureLevels:
            if level in answer:
                logger.info(f"模型分类结果: {level}")
                return level
                
        # 如果结果不在预期范围内，返回默认值
        logger.warning(f"模型返回了意外的答案: {answer}，使用默认分类")
        return "非结构化数据"  # 默认为非结构化数据
        
    except Exception as e:
        logger.error(f"调用模型API出错: {str(e)}")
        # 出错时返回默认分类
        return "非结构化数据"

def Classify(InputPath, OutputPath):
    """
    用于将不同的txt文件按照结构化程度进行分类
    
    优化点：
    - 批量处理文件提高效率
    - 使用线程池并行处理
    - 添加缓存减少API调用
    - 详细的日志和错误处理
    
    参数：
        InputPath: 输入文本目录
        OutputPath: 输出分类目录
    """
    # 获取线程安全的日志记录器
    logger = get_logger()
    start_time = time.time()
    
    # 记录开始处理
    logger.info(f"开始分类处理: InputPath={InputPath}, OutputPath={OutputPath}")
    
    try:
        # 创建三个子文件夹
        SD = os.path.join(OutputPath, "Structured_Data")
        SSD = os.path.join(OutputPath, "Semi-Structured_Data")
        USD = os.path.join(OutputPath, "Unstructured_Data")
        
        # 创建目录
        for dir_path in [SD, SSD, USD]:
            os.makedirs(dir_path, exist_ok=True)
            
        # 收集所有需要处理的文本文件
        files_to_process = []
        path = Path(InputPath)
        
        for filepath in path.rglob('*'):
            if not filepath.is_file() or not str(filepath).endswith('.txt'):
                continue
            files_to_process.append(filepath)
            
        total_files = len(files_to_process)
        logger.info(f"发现 {total_files} 个文本文件需要分类")
        
        if total_files == 0:
            logger.warning("没有找到需要分类的文本文件")
            return
            
        # 确定最佳线程数
        import multiprocessing
        max_workers = min(max(2, multiprocessing.cpu_count()), 10)
        logger.info(f"使用 {max_workers} 个线程并行分类")
        
        # 批量处理大小
        batch_size = 5
        
        # 记录处理统计
        processed = 0
        structured_count = 0
        semi_structured_count = 0
        unstructured_count = 0
        error_count = 0
        
        # 使用线程池并行处理文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 分批处理文件
            for i in range(0, total_files, batch_size):
                batch_files = files_to_process[i:min(i+batch_size, total_files)]
                
                # 创建任务
                future_to_file = {
                    executor.submit(classify_single_file, filepath, SD, SSD, USD): filepath
                    for filepath in batch_files
                }
                
                # 处理批次结果
                for future in concurrent.futures.as_completed(future_to_file):
                    filepath = future_to_file[future]
                    try:
                        result = future.result()
                        processed += 1
                        
                        # 更新统计信息
                        if result == "结构化数据":
                            structured_count += 1
                        elif result == "半结构化数据":
                            semi_structured_count += 1
                        elif result == "非结构化数据":
                            unstructured_count += 1
                            
                        # 每处理5个文件或达到总数时打印进度
                        if processed % 5 == 0 or processed == total_files:
                            progress = processed * 100 / total_files
                            logger.info(f"已分类 {processed}/{total_files} 文件 ({progress:.1f}%)")
                            
                    except Exception as e:
                        logger.error(f"分类文件 {filepath} 时出错: {str(e)}")
                        error_count += 1
        
        # 计算处理时间
        end_time = time.time()
        elapsed = end_time - start_time
        
        # 输出最终统计
        logger.info(f"分类处理完成。结构化: {structured_count}, 半结构化: {semi_structured_count}, "
                   f"非结构化: {unstructured_count}, 错误: {error_count}, 总耗时: {elapsed:.2f} 秒")
                   
    except Exception as e:
        logger.error(f"分类处理过程中出现未捕获的异常: {str(e)}")

def classify_single_file(filepath, sd_dir, ssd_dir, usd_dir):
    """
    分类单个文本文件
    
    功能：
    - 读取文本文件内容
    - 调用模型进行分类
    - 将文件移动到相应目录
    
    参数：
        filepath: 文本文件路径
        sd_dir: 结构化数据目录
        ssd_dir: 半结构化数据目录
        usd_dir: 非结构化数据目录
        
    返回：
        str: 分类结果
    """
    logger = get_logger()
    
    try:
        # 默认分类为非结构化数据
        classification = "非结构化数据"
        
        # 读取文件内容
        try:
            content = filepath.read_text(encoding='utf-8')
            # 计算内容哈希值，用于缓存
            content_hash = hash(content)
            
            # 调用缓存的查询函数
            classification = cached_query_model(content_hash, content)
        except Exception as e:
            logger.error(f"读取文件 {filepath} 时出错: {str(e)}")
            
        # 分类文件到对应目录
        Classify_in_Dir(filepath, classification, sd_dir, ssd_dir, usd_dir)
        
        return classification
    except Exception as e:
        logger.error(f"分类单个文件 {filepath} 时出错: {str(e)}")
        return "非结构化数据"  # 出错时默认为非结构化数据

# 使用缓存优化的API查询函数
def QuiryModel(content):
    """
    查询文本结构化程度的API接口
    
    优化点：
    - 使用缓存减少重复调用
    - 增强错误处理
    - 返回标准化结果
    
    参数：
        content: 待分类的文本内容
        
    返回：
        str: 分类结果
    """
    try:
        # 计算内容哈希值
        content_hash = hash(content)
        # 调用缓存的查询函数
        return cached_query_model(content_hash, content)
    except Exception as e:
        logger = get_logger()
        logger.error(f"查询模型时出错: {str(e)}")
        return "非结构化数据"  # 返回默认分类

Principle="""
结构化数据：数据是否以表格形式存在，每行和每列都有明确的字段和数据类型。\n
半结构化数据：数据是否包含键值对、分隔符或嵌套结构。\n
非结构化数据：数据是否为自由文本或多媒体内容，没有固定的格式。\n
"""

def Classify_in_Dir(filepath,answer,SD,SSD,USD):
    """将对应文件分类到对应的文件夹下面"""
    if answer == "结构化数据":
        copy_file(filepath,SD)
    elif answer == "半结构化数据":
        copy_file(filepath,SSD)
    else:
        copy_file(filepath,USD)
    return