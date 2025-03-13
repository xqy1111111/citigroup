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

# ===== 线程安全机制 =====
# 【线程本地存储】
# 线程本地存储是一种多线程编程技术，为每个线程创建单独的变量副本
# 避免多线程环境下共享可变状态导致的竞争条件和数据不一致问题
thread_local = threading.local()

# ===== 缓存机制实现 =====
# 【带超时的LRU缓存】
def lru_cache_with_timeout(maxsize=128, timeout=3600):
    """
    带超时的LRU缓存装饰器
    
    【高级缓存装饰器】
    这个装饰器是标准functools.lru_cache的增强版本，添加了超时功能。
    LRU(最近最少使用)缓存在保持固定大小的同时，优先淘汰最久未使用的项目。
    
    【并发优化点】
    1. 减少重复计算 - 缓存之前的调用结果，避免重复API调用
    2. 线程安全设计 - 使用锁机制保护缓存操作，支持多线程并发访问
    3. 超时机制 - 定期刷新缓存，确保数据不会过时
    4. 资源控制 - 限制缓存大小，避免内存泄漏
    
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
        # 【底层缓存】
        # Python标准库提供的lru_cache自身是线程安全的，
        # 但它不支持超时功能，所以需要额外实现
        func = functools.lru_cache(maxsize=maxsize)(func)
        # 保存最后访问时间
        func.lifetime = {}
        # 【线程安全锁】
        # RLock(可重入锁)允许同一线程多次获取锁而不会死锁
        # 保护缓存操作的原子性，特别是检查和更新lifetime字典时
        func.cache_lock = threading.RLock()
        
        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):
            # 检查缓存是否超时
            # 【关键并发处理点】
            # 使用lock确保在检查和更新缓存时的线程安全
            # 多个线程可能同时调用此函数，但获取锁后只有一个线程能执行临界区
            now = time.time()
            with func.cache_lock:
                # 检查键是否在缓存中
                # 【缓存键生成】
                # functools._make_key创建一个可哈希的缓存键，基于函数参数
                # 这允许将任意参数组合映射到缓存结果
                key = functools._make_key(args, kwargs, typed=False)
                if key in func.lifetime and now - func.lifetime[key] > timeout:
                    # 超时，删除缓存项
                    # 【缓存失效】
                    # 当发现缓存项过期时，清除整个缓存以简化实现
                    # 在实际生产系统中，可能需要更细粒度的缓存项管理
                    func.cache_info()  # 必须先调用，刷新内部状态
                    func.cache_clear()
                    func.lifetime.clear()
                
                # 调用函数并更新访问时间
                # 不论是缓存命中还是缓存未命中，都会更新访问时间
                result = func(*args, **kwargs)
                func.lifetime[key] = now
                return result
                
        return wrapped_func
    return wrapper_cache

# 获取线程安全的日志记录器
def get_logger():
    """
    获取线程安全的日志记录器
    
    【线程安全日志】
    在多线程环境中，日志记录可能是性能瓶颈和线程安全问题的来源。
    本函数通过以下方式解决这些问题：
    - 线程本地存储 - 每个线程有独立的logger对象
    - 线程标识 - 在日志名称中包含线程ID，便于追踪
    - 延迟初始化 - 只在需要时创建资源
    
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

# ===== API调用缓存优化 =====
# 【缓存的模型查询】
# 使用装饰器缓存模型查询结果，大幅减少API调用次数
# maxsize=1000限制缓存大小，避免内存泄漏
# timeout=1800设置30分钟超时，平衡缓存新鲜度和API调用次数
@lru_cache_with_timeout(maxsize=1000, timeout=1800)  # 缓存1000条记录，超时30分钟
def cached_query_model(content_hash, content):
    """
    带缓存的模型查询函数
    
    【缓存优化的API调用】
    由于模型API调用通常很昂贵（时间和成本），缓存是关键优化手段：
    - 使用内容哈希作为缓存键，避免重复调用
    - 设置缓存超时，确保数据不会过时
    - 错误处理保证即使API失败也能安全返回结果
    
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
        # 【API调用】
        # 这是系统中最耗时的操作，也是引入缓存的主要原因
        # 在高并发系统中，应考虑添加额外的限流和重试机制
        logger.info(f"调用模型API分类文本 (hash: {content_hash})")
        
        # 使用GLM-4或其他模型进行分类
        response = client.chat.completions.create(
        model="glm-4-flash",  # 请填写您要调用的模型名称
        messages=[
            {"role": "user",
             "content": f"现在需要你对以下文件内容：\n\n "
                        f"{content}\n\n "
                        f"深度分析该文件的结构化程度\n"
                        f"分类标准如下:\n"
                        f"{Principle}\n"
                        #f"回答其结构化程度是 较高、一般、较弱\n "
                        # f"注意你的回答只能是 '较高' 或者 '一般' 或者 '较弱'"
                        f"回答这个文件的数据属于 非结构化数据？结构化数据？还是 半结构化数据？\n"
                        f"注意你的回答只能是 结构化数据/半结构化数据/非结构化数据\n"
                        # f"注意你的回答只能是 非结构化数据/结构化数据/半结构化数据\n"
                        # f"另外还需要注意严格区分 半结构化数据/非结构化数据/结构化数据 \n"
                        # f"如果你在结构化与半结构化之间犹豫不定，以80%概率将其归于半结构化数据\n"
                        f"并且不用给出理由  直接回答是 结构化数据？半结构化数据？非结构化数据？ 即可"
             },
        ],
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
    
    【并行分类处理】
    本函数使用多线程并行处理文本分类任务，主要并发优化包括：
    - 线程池 - 使用ThreadPoolExecutor管理工作线程
    - 批量处理 - 将文件分批处理，减少线程创建和销毁的开销
    - 缓存机制 - 使用缓存减少对模型API的调用
    - 动态线程数 - 根据CPU核心数自动决定最佳线程数
    
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
        # 【输出目录初始化】
        # 创建分类子目录，每个子目录对应一种数据结构化级别
        SD = os.path.join(OutputPath, "Structured_Data")
        SSD = os.path.join(OutputPath, "Semi-Structured_Data")
        USD = os.path.join(OutputPath, "Unstructured_Data")
        
        # 创建目录 - 使用exist_ok=True确保线程安全
        for dir_path in [SD, SSD, USD]:
            os.makedirs(dir_path, exist_ok=True)
            
        # 收集所有需要处理的文本文件
        # 【任务收集阶段】
        # 在启动并行处理前，先扫描所有文件创建任务列表
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
        # 【线程池大小确定】
        # 线程数过少会限制并行度，线程数过多则会增加上下文切换的开销
        # 对于I/O密集型或网络请求密集型任务(如API调用)，可以使用较多线程
        import multiprocessing
        max_workers = min(max(2, multiprocessing.cpu_count()), 10)
        logger.info(f"使用 {max_workers} 个线程并行分类")
        
        # 批量处理大小
        # 【批处理策略】
        # 批处理可以减少任务调度和结果收集的开销，提高并行效率
        # 批大小应权衡并行度和调度开销，此处选择5作为合理值
        batch_size = 5
        
        # 记录处理统计
        # 【统计计数器】
        # 使用计数器跟踪处理结果，记录不同类型分类的数量
        processed = 0
        structured_count = 0
        semi_structured_count = 0
        unstructured_count = 0
        error_count = 0
        
        # 使用线程池并行处理文件
        # 【线程池执行】
        # ThreadPoolExecutor管理线程的创建、任务分配和资源回收
        # with语句确保线程池在使用后被正确关闭，防止资源泄漏
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 分批处理文件
            # 【批量调度】
            # 将文件分批提交给线程池，可以更好地控制内存使用和并行度
            for i in range(0, total_files, batch_size):
                batch_files = files_to_process[i:min(i+batch_size, total_files)]
                
                # 创建任务
                # 【任务提交】
                # executor.submit向线程池提交任务，并返回Future对象
                # future代表未来将要完成的操作，可以通过它获取结果或检查状态
                future_to_file = {
                    executor.submit(classify_single_file, filepath, SD, SSD, USD): filepath
                    for filepath in batch_files
                }
                
                # 处理批次结果
                # 【结果收集】
                # concurrent.futures.as_completed返回已完成的Future对象迭代器
                # 这样可以处理最先完成的任务结果，而不必按提交顺序等待
                for future in concurrent.futures.as_completed(future_to_file):
                    filepath = future_to_file[future]
                    try:
                        # 获取分类结果
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
    
    【工作线程函数】
    这个函数在线程池的工作线程中执行，设计考虑了线程安全性：
    - 使用线程安全的日志记录
    - 基于缓存减少昂贵的API调用
    - 异常处理避免线程崩溃
    - 无共享状态设计
    
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
        # 【文件读取】
        # 在多线程环境中，文件读取通常是安全的，只要每个线程读取不同的文件
        # 这里每个线程处理不同的filepath，所以不会有资源竞争
        try:
            content = filepath.read_text(encoding='utf-8')
            # 计算内容哈希值，用于缓存
            # 【缓存键生成】
            # 使用内容哈希作为缓存键，而不是文件路径
            # 这样相同内容的不同文件可以共享缓存结果
            content_hash = hash(content)
            
            # 调用缓存的查询函数
            # 【缓存调用点】
            # 这是缓存机制的关键应用点，相同内容的重复查询可以直接返回缓存结果
            # 大幅减少API调用次数，提高性能并降低成本
            classification = cached_query_model(content_hash, content)
        except Exception as e:
            logger.error(f"读取文件 {filepath} 时出错: {str(e)}")
            
        # 分类文件到对应目录
        # 【文件操作】
        # Classify_in_Dir函数负责将文件复制到对应的分类目录
        # 在多线程环境中，不同线程操作不同的源文件是安全的
        Classify_in_Dir(filepath, classification, sd_dir, ssd_dir, usd_dir)
        
        return classification
    except Exception as e:
        logger.error(f"分类单个文件 {filepath} 时出错: {str(e)}")
        return "非结构化数据"  # 出错时默认为非结构化数据

# 使用缓存优化的API查询函数
def QuiryModel(content):
    """
    查询文本结构化程度的API接口
    
    【API查询包装函数】
    这是对cached_query_model的简单包装，便于其他代码调用：
    - 计算内容哈希值作为缓存键
    - 利用缓存机制减少API调用
    - 提供统一的错误处理
    
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
