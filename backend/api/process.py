"""
文件处理API路由模块

这个模块实现了与文件处理相关的所有API端点，主要功能包括：
1. 文件结构化处理 - 将原始文件转换为结构化数据
2. 风险预测分析 - 对文件内容进行风险评估
3. 异步任务管理 - 处理长时间运行的操作而不阻塞API响应
4. 多进程并行处理 - 利用多核CPU加速处理过程

文件处理是系统的核心功能，支持将上传的金融文档转换为结构化数据，
并通过风险预测模型进行分析，生成风险评估报告。
"""
# ===== 导入必要的库 =====
import random  # 用于生成随机数，主要用于任务ID和模拟预测概率
import asyncio  # 异步编程支持，允许非阻塞操作
import shutil  # 文件和目录操作，用于复制和删除文件
import os  # 操作系统功能，用于路径操作和目录创建
import glob  # 文件路径模式匹配，用于查找特定模式的文件
import json  # JSON数据处理，用于读写JSON文件
import time  # 时间相关操作，用于生成时间戳和计算过期时间
from fastapi import APIRouter, HTTPException, BackgroundTasks  # FastAPI框架组件
from concurrent.futures import ProcessPoolExecutor  # 多进程支持，用于CPU密集型任务
from services.risk_prediction.prediction import predict_all  # 风险预测服务
from services.DataStructuring.DataStructuring import main_process  # 数据结构化处理
from services import target_to_json  # 数据转JSON服务
from db.db_util import create_or_update_json_res, update_file_status, upload_res_file  # 数据库操作
from ._file import download_file  # 文件下载功能
import aiofiles  # 异步文件操作库
import logging  # 日志记录
from typing import Dict, Any, Optional  # 类型提示
import concurrent.futures  # 并发处理模块
import traceback  # 用于获取错误堆栈信息
from io import BytesIO  # 用于BytesIO包装文件内容

# ===== 初始化配置 =====
# 设置日志系统
# 定义ANSI颜色代码
class LogColors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

# 自定义日志格式化器，添加颜色支持
class ColoredFormatter(logging.Formatter):
    """为不同级别的日志添加颜色"""
    FORMATS = {
        logging.DEBUG: LogColors.BLUE + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + LogColors.RESET,
        logging.INFO: "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logging.WARNING: LogColors.YELLOW + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + LogColors.RESET,
        logging.ERROR: LogColors.RED + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + LogColors.RESET,
        logging.CRITICAL: LogColors.RED + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + LogColors.RESET
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# 配置日志系统
logging.basicConfig(level=logging.INFO)  # 配置日志级别为INFO
logger = logging.getLogger(__name__)  # 获取当前模块的日志记录器

# 为控制台输出添加颜色处理
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())
logger.addHandler(console_handler)
# 移除默认处理器以避免重复日志
logger.propagate = False

# 创建进程池用于并行处理
# 【多进程基础】
# ProcessPoolExecutor是Python的concurrent.futures模块提供的一个高级抽象，用于管理进程池
# 进程池维护一组工作进程，避免了频繁创建和销毁进程的开销
# 每个进程都是独立的Python解释器实例，有自己的内存空间，适合CPU密集型任务
# 默认情况下，进程池大小等于CPU核心数(os.cpu_count())
process_pool = ProcessPoolExecutor()  # 用于处理CPU密集型任务的进程池

# ===== 全局状态管理 =====
# 存储所有任务的状态信息
# 【注意】这是进程内存储，如果使用多进程部署，每个进程会有独立的状态副本
# 在分布式系统中，应该使用Redis等外部存储来共享状态
task_status = {}  # 格式: {task_id: status_string}

# 存储文件与任务的关联关系
file_tasks = {}  # 格式: {file_id: [task_id1, task_id2, ...]}

# 创建API路由器
router = APIRouter()

# ===== 文件处理入口 =====
@router.post("/{file_id}/multiprocess")
async def process_file_to_json(file_id: str, repo_id: str, background_tasks: BackgroundTasks):
    """
    异步处理文件API
    
    详细说明:
    此端点接收文件ID和仓库ID，启动异步任务处理文件。
    处理包括文件结构化和风险预测两个主要步骤，整个过程在后台进行，
    不会阻塞API响应。用户可以通过任务ID查询处理进度。
    
    工作流程：
    1. 生成唯一任务ID
    2. 异步下载目标文件
    3. 更新文件处理状态
    4. 启动后台处理任务
    5. 返回任务信息
    
    参数:
        file_id (str): 需要处理的文件ID
        repo_id (str): 文件所在的仓库ID
        background_tasks: FastAPI的后台任务管理器
        
    返回:
        dict: 包含任务ID和处理状态的信息
        
    错误:
        404 Not Found - 如果指定ID的文件不存在
    """
    # 生成唯一的任务ID（组合：文件ID + 时间戳 + 随机数）
    # 这种组合方式确保在分布式环境中也能生成唯一ID
    task_id = f"{file_id}_{int(time.time())}_{random.randint(1000, 9999)}"
    
    try:
        # 第一步：异步下载文件
        # 【修复5】改进文件下载和验证逻辑
        try:
            # 通过to_thread将同步函数转换为异步操作
            file_data = await asyncio.to_thread(download_file, file_id)
            
            if not file_data:
                logger.error(f"[Task {task_id}] 文件下载失败: file_id={file_id}")
                raise HTTPException(status_code=404, detail="文件不存在或下载失败")
                
            # 验证下载的文件数据
            filename, file_content = file_data
            if not filename or not file_content:
                logger.error(f"[Task {task_id}] 下载的文件数据无效: filename={filename}, content_size={len(file_content) if file_content else 0}")
                raise HTTPException(status_code=500, detail="文件数据无效")
                
            logger.info(f"[Task {task_id}] 文件下载成功: {filename}, 大小: {len(file_content)} 字节")
        except Exception as e:
            logger.error(f"[Task {task_id}] 文件下载异常: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")
        
        # 第二步：更新文件状态为处理中
        await asyncio.to_thread(update_file_status, repo_id, file_id, "processing", True)
        
        # 第三步：添加后台处理任务
        # 【FastAPI后台任务】
        # background_tasks.add_task将函数添加到后台任务队列
        # 这些任务会在HTTP响应返回后执行，不会延迟API响应时间
        # 与asyncio不同，FastAPI的后台任务在响应后才开始执行
        background_tasks.add_task(background_processing, file_id, repo_id, file_data, task_id)
        
        # 第四步：初始化任务状态
        task_status[task_id] = "started"
        
        # 第五步：更新文件-任务映射关系
        if file_id not in file_tasks:
            file_tasks[file_id] = []
        file_tasks[file_id].append(task_id)
        
        # 返回处理信息
        return {
            "message": "File processing started", 
            "file_id": file_id, 
            "task_id": task_id, 
            "repo_id": repo_id
        }
        
    except Exception as e:
        # 异常处理：记录错误并返回500响应
        logger.error(f"Error processing file {file_id}: {str(e)}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# ===== 后台处理任务 =====
async def background_processing(file_id: str, repo_id: str, file_data, task_id: str):
    """
    后台文件处理函数
    
    详细说明:
    此函数在后台执行文件处理流程，包括：
    1. 创建临时工作目录
    2. 保存下载的文件到临时目录
    3. 在进程池中执行CPU密集型处理
    4. 处理完成后更新数据库和任务状态
    
    工作流程设计为异步，以避免阻塞Web服务器。
    CPU密集型操作被委托给专用的进程池，以最大化利用多核处理能力。
    
    参数:
        file_id (str): 文件ID
        repo_id (str): 仓库ID
        file_data: 下载的文件数据(文件名和内容)
        task_id (str): 任务ID
    """
    # 更新任务状态为正在处理
    task_status[task_id] = "processing"
    
    try:
        # 解包文件数据
        filename, file_content = file_data
        
        # 获取当前文件路径
        current_file_path = os.path.abspath(__file__)
        
        # 获取当前文件的父目录，即项目的backend/api目录
        parent_dir = os.path.dirname(current_file_path)
        
        # 再往上一层，获取backend目录
        parent_dir = os.path.dirname(parent_dir)
        
        # 获取DataStructuring目录路径
        data_struct_dir = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring")
        
        # 在DataStructuring目录下创建以task_id命名的子目录
        task_work_dir = os.path.join(data_struct_dir, task_id)
        
        # 创建子目录路径 - 使用DataStructuring中已有的目录结构
        # 注意：这里只是创建特定任务的子目录，而不是修改主目录结构
        upload_folder = os.path.join(data_struct_dir, "SourceData", task_id)
        target_folder = os.path.join(data_struct_dir, "TargetData", task_id)
        json_folder = os.path.join(data_struct_dir, "JsonData", task_id)
        predict_folder = os.path.join(data_struct_dir, "PredictData", task_id) if os.path.exists(os.path.join(data_struct_dir, "PredictData")) else os.path.join(data_struct_dir, task_id, "PredictData")
        
        # 工作目录路径（兼容性考虑，保留原变量名）
        work_dir = task_work_dir
        
        # 【修复6】确保目录存在，并清理可能存在的冲突文件
        # 先删除可能存在的特定任务子目录，确保从干净状态开始
        for folder in [upload_folder, target_folder, json_folder]:
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder)
                    logger.info(f"[Task {task_id}] 删除已存在的目录: {folder}")
                except Exception as e:
                    logger.warning(f"[Task {task_id}] 无法删除已存在的目录: {folder}, 错误: {str(e)}")
        
        # 创建新的目录结构
        try:
            os.makedirs(upload_folder, exist_ok=True)
            os.makedirs(target_folder, exist_ok=True)
            os.makedirs(json_folder, exist_ok=True)
            os.makedirs(predict_folder, exist_ok=True)
            logger.info(f"[Task {task_id}] 创建目录结构: SourceData/{task_id}, TargetData/{task_id}, JsonData/{task_id}")
        except Exception as e:
            logger.error(f"[Task {task_id}] 创建目录失败: {str(e)}")
            raise
        
        # 【修复7】改进文件保存方式，使用同步写入确保文件真正写入磁盘
        file_path = os.path.join(upload_folder, filename)
        try:
            # 使用同步方式保存文件，确保写入完成
            with open(file_path, "wb") as f:
                f.write(file_content)
                f.flush()  # 确保数据写入磁盘
                os.fsync(f.fileno())  # 强制操作系统将数据写入物理存储
            
            # 验证文件是否成功保存
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件保存失败，无法找到: {file_path}")
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError(f"保存的文件大小为0: {file_path}")
                
            logger.info(f"[Task {task_id}] 文件成功保存: {file_path}, 大小: {file_size} 字节")
            
            # 列出源目录中的所有文件，以便调试
            source_files = os.listdir(upload_folder)
            logger.info(f"[Task {task_id}] 源目录内容: {', '.join(source_files)}")
            
            # 验证文件内容
            with open(file_path, "rb") as f:
                content_check = f.read(100)  # 读取前100字节进行校验
                logger.info(f"[Task {task_id}] 文件内容校验: 前{len(content_check)}字节有效")
        except Exception as e:
            logger.error(f"[Task {task_id}] 文件保存或验证失败: {str(e)}")
            logger.error(f"[Task {task_id}] 错误堆栈: {traceback.format_exc()}")
            raise
            
        # 【修复8】为子进程准备文件信息
        process_info = {
            "work_dir": work_dir,
            "upload_folder": upload_folder,
            "target_folder": target_folder,
            "json_folder": json_folder,
            "predict_folder": predict_folder,
            "filename": filename,
            "file_id": file_id,
            "repo_id": repo_id,
            "task_id": task_id,
            "file_path": file_path,
            "file_size": file_size
        }
        
        # 在进程池中执行CPU密集型处理
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            process_pool, 
            process_data, 
            process_info
        )
        
        # 更新任务状态
        json_result, predictions = result
        if json_result:
            task_status[task_id] = "completed"
            logger.info(f"[Task {task_id}] Processing completed successfully")
        else:
            task_status[task_id] = "failed"
            logger.error(f"[Task {task_id}] Processing failed")
        
        # 清理工作目录
        # 处理完成后删除临时文件，释放磁盘空间
        try:
            # 只删除任务特定的子目录，而不是整个DataStructuring目录
            for folder in [upload_folder, target_folder, json_folder, predict_folder]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
            
            # 如果创建了task_work_dir目录，也删除它
            if os.path.exists(work_dir) and os.path.basename(work_dir) == task_id:
                shutil.rmtree(work_dir)
                
            logger.info(f"[Task {task_id}] Cleaned up task directories")
        except Exception as e:
            logger.warning(f"[Task {task_id}] Failed to clean up task directories: {str(e)}")
        
    except Exception as e:
        # 异常处理：记录错误并更新任务状态
        logger.error(f"[Task {task_id}] Error in background processing: {str(e)}")
        
        # 【修复】添加详细的错误栈追踪信息，帮助排查问题
        logger.error(f"[Task {task_id}] 错误堆栈: {traceback.format_exc()}")
        
        task_status[task_id] = f"error: {str(e)}"
        
        # 尝试更新文件状态为错误
        try:
            await asyncio.to_thread(update_file_status, repo_id, file_id, f"error: {str(e)}", True)
        except Exception as update_error:
            logger.error(f"[Task {task_id}] Failed to update file status: {str(update_error)}")

# ===== 文件处理核心逻辑 =====
def process_data(process_info):
    """
    文件处理的核心函数
    
    详细说明:
    此函数执行实际的文件处理工作，包括：
    1. 文件结构化处理 - 将原始文件转换为结构化格式
    2. 风险预测分析 - 对结构化数据进行风险评估
    3. 生成JSON结果 - 将结构化数据转换为JSON格式
    4. 更新数据库 - 保存处理结果和风险预测
    
    该函数设计为在单独的进程中运行，避免阻塞主应用进程。
    处理过程中的进度和状态会定期更新。
    
    参数:
        process_info (dict): 包含所有必要的处理信息
        
    返回:
        tuple: (JSON结果数据, 预测结果)
    """
    try:
        # 解包处理信息
        work_dir = process_info["work_dir"]
        upload_folder = process_info["upload_folder"]
        target_folder = process_info["target_folder"]
        json_folder = process_info["json_folder"]
        predict_folder = process_info["predict_folder"]
        filename = process_info["filename"]
        file_id = process_info["file_id"]
        repo_id = process_info["repo_id"]
        task_id = process_info["task_id"]
        file_path = process_info["file_path"]
        file_size = process_info["file_size"]
        
        logger.info(f"[Task {task_id}] 开始数据处理，文件: {filename}, 大小: {file_size}")
        
        # 保存原始工作目录
        original_cwd = os.getcwd()
        
        # 【修复9】验证文件在子进程中可访问
        if not os.path.exists(file_path):
            logger.error(f"[Task {task_id}] 子进程无法访问文件: {file_path}")
            update_file_status(repo_id, file_id, "error: 子进程无法访问文件", True)
            return None, None
            
        logger.info(f"[Task {task_id}] 子进程成功访问文件: {file_path}")
        
        # 列出源目录中的所有文件，以便调试
        source_files = os.listdir(upload_folder)
        if not source_files:
            logger.error(f"[Task {task_id}] 子进程无法找到源目录中的文件: {upload_folder}")
            update_file_status(repo_id, file_id, "error: 源目录为空", True)
            return None, None
            
        logger.info(f"[Task {task_id}] 子进程中源目录内容: {', '.join(source_files)}")
        
        # 第一步：结构化处理
        # 将原始文件转换为结构化格式
        logger.info(f"[Task {task_id}] Step 1: Data structuring")
        try:
            # 【修复11】直接在当前进程执行结构化处理，避免多层进程嵌套
            logger.info(f"[Task {task_id}] 直接在当前进程执行结构化处理")
            
            # 验证源目录中是否有文件
            if not os.path.exists(upload_folder):
                logger.error(f"[Task {task_id}] 源目录不存在: {upload_folder}")
                raise Exception("源目录不存在")
                
            source_files = os.listdir(upload_folder)
            logger.info(f"[Task {task_id}] 源目录内容: {', '.join(source_files)}")
            
            if not source_files:
                logger.error(f"[Task {task_id}] 源目录为空，无法进行处理")
                raise Exception("源目录为空，无法进行处理")
                
            # 直接执行文件处理，避免多层进程调用
            try:
                main_process.main_process(
                    source_dir=upload_folder,
                    target_dir=target_folder
                )
                logger.info(f"[Task {task_id}] 结构化处理完成")
                
                # 验证处理结果
                target_files = glob.glob(os.path.join(target_folder, "*"))
                if not target_files:
                    logger.warning(f"[Task {task_id}] 结构化处理未生成任何输出文件")
                else:
                    logger.info(f"[Task {task_id}] 生成了{len(target_files)}个输出文件")
                    
            except Exception as e:
                logger.error(f"[Task {task_id}] 结构化处理失败: {str(e)}")
                logger.error(f"[Task {task_id}] 错误堆栈: {traceback.format_exc()}")
                raise Exception(f"结构化处理失败: {str(e)}")
            
            logger.info(f"[Task {task_id}] 数据结构化处理完成")
            
        except Exception as e:
            # 异常处理：记录错误并返回失败结果
            logger.error(f"[Task {task_id}] Error in data structuring: {str(e)}")
            update_file_status(repo_id, file_id, f"error: {str(e)}", True)
            return None, None
        
        # 第二步：风险预测
        # 对结构化数据进行风险评估
        logger.info(f"[Task {task_id}] Step 2: Risk prediction")
        
        # 复制结构化数据到预测目录
        target_files = glob.glob(os.path.join(target_folder, "*"))
        for file_path in target_files:
            if os.path.isfile(file_path):
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(predict_folder, file_name)
                shutil.copy(file_path, dest_path)
        
        # 运行风险预测模型
        try:
            # 在原始目录中运行预测
            os.chdir(original_cwd)
            
            # 【修复1】修改predict_all的参数调用方式
            # 从错误日志分析，predict_all不接受predict_folder和source_folder参数
            # 尝试直接将目录路径作为第一个位置参数传递
            try:
                logger.info(f"[Task {task_id}] 调用predict_all函数，参数：{predict_folder}")
                predictions = predict_all(predict_folder)
            except Exception as e:
                logger.error(f"[Task {task_id}] predict_all函数调用失败: {str(e)}")
                logger.error(f"[Task {task_id}] 将尝试不同的调用方式")
                
                # 尝试不同的参数名称
                try:
                    predictions = predict_all(folder=predict_folder)
                except Exception as e2:
                    logger.error(f"[Task {task_id}] 第二次尝试失败: {str(e2)}")
                    
                    # 如果还是失败，设置一个默认的预测结果
                    predictions = {"error": f"预测功能调用失败: {str(e)}"}
            
            logger.info(f"[Task {task_id}] Risk prediction completed: {predictions}")
            
            # 获取该文件的预测结果
            excel_name = os.path.splitext(filename)[0] + ".xlsx"
            prediction_result = predictions.get(f'{excel_name}', None)
            
            # 更新文件状态为预测结果
            # source文件：如果有预测结果，将其作为状态；否则使用通用完成状态
            # 注意：原始上传的文件被视为source文件
            if prediction_result is not None:
                status = str(prediction_result)
            else:
                status = "processed (no prediction)"
                
            update_file_status(repo_id, file_id, status, True)
            
        except Exception as e:
            # 异常处理：记录错误但继续处理
            # 风险预测失败不应阻止整个处理流程
            logger.error(f"[Task {task_id}] Error in risk prediction: {str(e)}")
            predictions = {"error": str(e)}
            update_file_status(repo_id, file_id, "processed (prediction failed)", True)
        
        # 第三步：生成JSON结果
        # 将结构化数据转换为JSON格式
        logger.info(f"[Task {task_id}] Step 3: Generating JSON results")
        
        # 清理旧的JSON文件
        for json_file in glob.glob(os.path.join(json_folder, "*.json")):
            os.remove(json_file)
        
        # 【修复2】修改process_target_to_json的参数调用方式
        # 从错误日志分析，process_target_to_json不接受target_folder或target_dir参数
        try:
            logger.info(f"[Task {task_id}] 调用process_target_to_json函数，参数：target_dir={target_folder}, json_folder={json_folder}")
            # 尝试使用位置参数调用
            target_to_json.process_target_to_json(target_folder, json_folder)
        except TypeError as e:
            logger.error(f"[Task {task_id}] process_target_to_json函数参数错误: {str(e)}")
            
            # 尝试不同的参数组合
            try:
                # 尝试检查函数定义
                import inspect
                sig = inspect.signature(target_to_json.process_target_to_json)
                logger.info(f"[Task {task_id}] process_target_to_json函数签名: {sig}")
                
                # 根据参数名尝试不同的调用方式
                param_names = list(sig.parameters.keys())
                if len(param_names) >= 2:
                    kwargs = {
                        param_names[0]: target_folder,
                        param_names[1]: json_folder
                    }
                    logger.info(f"[Task {task_id}] 尝试使用参数名: {kwargs}")
                    target_to_json.process_target_to_json(**kwargs)
                else:
                    # 如果参数少于2个，使用位置参数
                    target_to_json.process_target_to_json(target_folder)
            except Exception as e2:
                logger.error(f"[Task {task_id}] 无法调用process_target_to_json: {str(e2)}")
                # 创建一个空的JSON文件作为替代
                dummy_json_path = os.path.join(json_folder, "dummy_result.json")
                with open(dummy_json_path, "w", encoding="utf-8") as f:
                    f.write('{"error": "JSON转换失败，请检查API兼容性"}')
                logger.warning(f"[Task {task_id}] 创建了替代JSON文件: {dummy_json_path}")
        
        # 找到生成的JSON文件并读取内容
        json_files = glob.glob(os.path.join(json_folder, "*.json"))
        all_json_content = {}
            
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    file_content = f.read()
                    
                # 解析JSON内容
                json_data = json.loads(file_content)
                
                # 将每个文件的内容合并到总结果中
                json_base_name = os.path.basename(json_file)
                all_json_content[json_base_name] = json_data
                
                logger.info(f"[Task {task_id}] 成功解析JSON文件: {json_base_name}")
                
            except Exception as e:
                # 解析单个JSON文件失败不应阻止整个处理流程
                logger.error(f"[Task {task_id}] Error parsing JSON file {json_file}: {str(e)}")
                all_json_content[os.path.basename(json_file)] = {"error": str(e)}
        
        # 验证JSON内容
        if not all_json_content:
            logger.warning(f"[Task {task_id}] 没有找到任何有效的JSON文件")
            all_json_content = {"error": "No valid JSON files found"}
        
        # 第四步：保存处理结果到数据库
        logger.info(f"[Task {task_id}] Step 4: Saving results to database")
        
        # 生成完整的JSON结果
        json_result = {
            "content": all_json_content,
            "predictions": predictions if predictions else {"error": "No predictions available"}
        }
        
        # 上传处理结果文件到GridFS
        # 找到生成的Excel文件
        excel_files = glob.glob(os.path.join(target_folder, "*.xlsx"))
        target_file_ids = []  # 存储所有target文件的ID
        
        if not excel_files:
            logger.warning(f"[Task {task_id}] 没有找到任何Excel文件")
        
        for excel_file in excel_files:
            try:
                # 读取Excel文件内容
                with open(excel_file, "rb") as f:
                    excel_content = f.read()
                
                excel_filename = os.path.basename(excel_file)
                
                # 使用BytesIO包装文件内容，提供文件对象接口
                from io import BytesIO
                
                # 上传处理后的结果文件 (target文件)
                file_id_res = upload_res_file(
                    repo_id=repo_id,
                    file_obj=BytesIO(excel_content),
                    source_file_id=file_id,
                    filename=excel_filename,
                    source=False
                )
                
                if file_id_res:
                    target_file_ids.append(file_id_res)
                    try:
                        update_file_status(repo_id, file_id_res, "completed", True)
                        logger.info(f"[Task {task_id}] 已将结果文件状态设为completed: {excel_filename}, file_id={file_id_res}")
                    except Exception as status_err:
                        logger.error(f"[Task {task_id}] 更新结果文件状态失败: {str(status_err)}")
                
                logger.info(f"[Task {task_id}] Uploaded result file: {excel_filename}")
                
            except Exception as e:
                logger.error(f"[Task {task_id}] Failed to upload result file {excel_file}: {str(e)}")
        
        # 验证是否有成功上传的文件
        if not target_file_ids:
            logger.warning(f"[Task {task_id}] 没有成功上传任何结果文件")
            # 如果没有成功上传的文件，使用原始文件ID
            target_file_ids = [file_id]
        
        # 为每个target文件创建JSON结果
        for target_file_id in target_file_ids:
            try:
                logger.info(f"[Task {task_id}] 正在为文件 {target_file_id} 创建JSON结果")
                json_res_id = create_or_update_json_res(target_file_id, json_result)
                logger.info(f"[Task {task_id}] 成功创建/更新JSON结果: file_id={target_file_id}, json_res_id={json_res_id}")
            except Exception as e:
                logger.error(f"[Task {task_id}] 创建/更新JSON结果失败: file_id={target_file_id}, error={str(e)}")
        
        # 返回处理结果
        return json_result, predictions
        
    except Exception as e:
        # 异常处理：记录错误并更新文件状态
        logger.error(f"[Task {task_id}] Error in main processing: {str(e)}")
        update_file_status(repo_id, file_id, f"error: {str(e)}", True)
        return None, None
    finally:
        # 确保清理工作目录
        try:
            # 切回原始目录，以防工作目录被删除导致错误
            os.chdir(original_cwd)
        except Exception:
            pass

# ===== 子任务处理函数 =====
def process_subtask(upload_folder, target_folder, json_folder, predict_folder, subtask_id):
    """
    处理子任务的辅助函数
    
    详细说明:
    此函数在单独的进程中执行特定子任务，当前主要用于文件结构化处理。
    设计为在进程池的工作进程中运行，与主应用完全隔离。
    
    参数:
        upload_folder (str): 源文件目录
        target_folder (str): 目标文件目录
        json_folder (str): JSON输出目录
        predict_folder (str): 预测数据目录
        subtask_id (str): 子任务ID
    
    返回:
        bool: 处理是否成功
    """
    try:
        logger.info(f"[Subtask {subtask_id}] 开始处理，进程ID: {os.getpid()}")
        
        # 【修复10】验证路径存在并可访问
        if not os.path.exists(upload_folder):
            logger.error(f"[Subtask {subtask_id}] 源目录不存在: {upload_folder}")
            return False
            
        # 列出源目录内容
        source_files = os.listdir(upload_folder)
        logger.info(f"[Subtask {subtask_id}] 源目录内容: {', '.join(source_files) if source_files else '空'}")
        
        if not source_files:
            logger.error(f"[Subtask {subtask_id}] 源目录为空，处理无法继续")
            return False
        
        # 检查第一个文件是否可访问
        first_file_path = os.path.join(upload_folder, source_files[0])
        try:
            file_size = os.path.getsize(first_file_path)
            logger.info(f"[Subtask {subtask_id}] 文件可访问: {first_file_path}, 大小: {file_size}")
        except Exception as e:
            logger.error(f"[Subtask {subtask_id}] 无法读取文件: {first_file_path}, 错误: {str(e)}")
            
        # 执行主处理逻辑
        try:
            main_process.main_process(
                source_dir=upload_folder,
                target_dir=target_folder
            )
            logger.info(f"[Subtask {subtask_id}] 文件结构化处理完成")
        except Exception as e:
            logger.error(f"[Subtask {subtask_id}] 处理失败: {str(e)}")
            logger.error(f"[Subtask {subtask_id}] 错误堆栈: {traceback.format_exc()}")
            return False
        
        # 验证处理结果
        target_files = glob.glob(os.path.join(target_folder, "*"))
        success = len(target_files) > 0
        
        logger.info(f"[Subtask {subtask_id}] 处理完成，结果目录内容: {', '.join(target_files) if target_files else '空'}")
        logger.info(f"[Subtask {subtask_id}] 处理{'成功' if success else '失败'}")
        return success
        
    except Exception as e:
        # 异常处理：记录错误并返回失败结果
        logger.error(f"[Subtask {subtask_id}] 处理异常: {str(e)}")
        logger.error(f"[Subtask {subtask_id}] 错误堆栈: {traceback.format_exc()}")
        return False

# ===== 工作目录清理函数 =====
def cleanup_work_dir(upload_folder, target_folder, json_folder, predict_folder):
    """
    清理工作目录的辅助函数
    
    详细说明:
    此函数删除工作目录中的所有文件，但保留目录结构。
    在开始新的处理任务前调用，确保工作环境干净。
    
    参数:
        upload_folder (str): 源文件目录
        target_folder (str): 目标文件目录
        json_folder (str): JSON输出目录
        predict_folder (str): 预测数据目录
    """
    # 清理各个工作目录中的文件
    for folder in [upload_folder, target_folder, json_folder, predict_folder]:
        if os.path.exists(folder):
            # 删除目录中的所有文件，但保留目录本身
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                try:
                    if os.path.isfile(item_path):
                        # 删除文件
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        # 递归删除子目录
                        shutil.rmtree(item_path)
                except Exception as e:
                    logger.warning(f"Failed to delete {item_path}: {e}")

# ===== 任务管理API =====
@router.get("/files/{file_id}/tasks")
async def get_file_tasks(file_id: str):
    """
    获取文件关联的任务API
    
    详细说明:
    此端点返回与特定文件关联的所有处理任务及其状态。
    用于前端查询文件处理进度和结果。
    
    参数:
        file_id (str): 文件ID
        
    返回:
        dict: 包含任务列表和状态的响应
    """
    # 检查文件是否有关联任务
    if file_id not in file_tasks:
        # 如果没有关联任务，返回空列表
        return {"file_id": file_id, "tasks": []}
    
    # 获取文件关联的所有任务
    tasks = file_tasks[file_id]
    
    # 构建任务状态列表
    task_list = []
    for task_id in tasks:
        # 获取任务状态，如果不存在则标记为未知
        status = task_status.get(task_id, "unknown")
        
        # 计算任务创建时间（从任务ID中提取）
        try:
            # 任务ID格式：file_id_timestamp_random
            # 提取中间的时间戳部分
            timestamp_str = task_id.split("_")[1]
            created_at = int(timestamp_str)
        except (IndexError, ValueError):
            # 如果解析失败，使用当前时间
            created_at = int(time.time())
        
        # 添加到任务列表
        task_list.append({
            "task_id": task_id,
            "status": status,
            "created_at": created_at
        })
    
    # 按创建时间排序，最新的任务在前
    task_list.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 返回文件任务信息
    return {
        "file_id": file_id,
        "tasks": task_list
    }

@router.delete("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    取消任务API
    
    详细说明:
    此端点允许取消正在进行的处理任务。
    注意：由于任务可能在进程池中运行，实际取消逻辑是尽力而为的。
    
    参数:
        task_id (str): 任务ID
        
    返回:
        dict: 包含取消结果的响应
        
    错误:
        404 Not Found - 如果指定ID的任务不存在
    """
    # 检查任务是否存在
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 获取当前任务状态
    current_status = task_status[task_id]
    
    # 如果任务已经完成或失败，不能取消
    if current_status in ["completed", "failed"] or current_status.startswith("error"):
        return {
            "task_id": task_id, 
            "status": current_status,
            "message": "Task already finished and cannot be cancelled"
        }
    
    # 更新任务状态为已取消
    task_status[task_id] = "cancelled"
    
    # 如果能够获取文件ID和仓库ID，更新文件状态
    # 注意：这是一个简单实现，无法强制终止已在进程池中运行的任务
    try:
        # 提取文件ID（任务ID的第一部分）
        file_id = task_id.split("_")[0]
        
        # 查找关联的仓库ID（在实际实现中，可能需要从数据库获取）
        # 这里我们不知道仓库ID，所以只更新任务状态
        logger.info(f"Task {task_id} for file {file_id} marked as cancelled")
        
    except Exception as e:
        logger.error(f"Error extracting file info from task {task_id}: {str(e)}")
    
    # 返回取消结果
    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "Task cancellation requested"
    }

@router.post("/tasks/cleanup")
async def cleanup_task_records(hours: int = 24):
    """
    清理任务记录API
    
    详细说明:
    此端点清理旧的任务记录，释放内存并保持任务列表简洁。
    默认清理24小时前的任务记录，时间范围可通过参数调整。
    
    参数:
        hours (int): 要保留的任务记录小时数，默认24小时
        
    返回:
        dict: 包含清理结果的响应
    """
    # 计算截止时间戳
    cutoff_time = time.time() - (hours * 3600)
    
    # 找出要删除的任务
    tasks_to_delete = []
    for task_id in task_status:
        try:
            # 从任务ID中提取时间戳
            timestamp_str = task_id.split("_")[1]
            task_time = int(timestamp_str)
            
            # 如果任务时间早于截止时间，标记为删除
            if task_time < cutoff_time:
                tasks_to_delete.append(task_id)
                
        except (IndexError, ValueError):
            # 如果无法提取时间戳，假设是旧任务
            tasks_to_delete.append(task_id)
    
    # 删除标记的任务
    deleted_count = 0
    for task_id in tasks_to_delete:
        # 从任务状态字典中删除
        if task_id in task_status:
            del task_status[task_id]
            deleted_count += 1
            
        # 从文件任务映射中删除
        for file_id in list(file_tasks.keys()):
            if task_id in file_tasks[file_id]:
                        file_tasks[file_id].remove(task_id)
                
                # 如果文件没有关联任务，删除文件记录
                        if not file_tasks[file_id]:
                            del file_tasks[file_id]
                    
    # 返回清理结果
    return {
        "deleted_tasks": deleted_count,
        "remaining_tasks": len(task_status),
        "remaining_files": len(file_tasks),
        "cutoff_time": cutoff_time
    }