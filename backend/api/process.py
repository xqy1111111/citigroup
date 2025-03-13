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

# ===== 初始化配置 =====
# 设置日志系统
logging.basicConfig(level=logging.INFO)  # 配置日志级别为INFO
logger = logging.getLogger(__name__)  # 获取当前模块的日志记录器

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
        # 【异步编程基础】
        # asyncio.to_thread将同步函数转换为异步操作，避免阻塞事件循环
        # 这使得同步函数download_file在后台线程执行，不阻塞Web服务器
        file_data = await asyncio.to_thread(download_file, file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
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
        
        # 创建工作目录路径
        # 每个任务有自己的工作目录，避免多个任务之间的文件冲突
        work_dir = os.path.join(parent_dir, "work_dirs", task_id)
        
        # 创建子目录路径
        upload_folder = os.path.join(work_dir, "SourceData")
        target_folder = os.path.join(work_dir, "TargetData")
        json_folder = os.path.join(work_dir, "JsonData")
        predict_folder = os.path.join(work_dir, "PredictData")
        
        # 创建目录结构
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(target_folder, exist_ok=True)
        os.makedirs(json_folder, exist_ok=True)
        os.makedirs(predict_folder, exist_ok=True)
        
        # 保存文件到上传目录
        file_path = os.path.join(upload_folder, filename)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        
        logger.info(f"[Task {task_id}] File saved to {file_path}, starting processing")
        
        # 在进程池中执行CPU密集型处理
        # 【并行处理】
        # 使用进程池执行process_data函数，避免阻塞Web服务器
        # 这允许多个文件并行处理，充分利用多核CPU
        # 对于CPU密集型任务，多进程比多线程更有效
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            process_pool, 
            process_data, 
            work_dir,
            upload_folder, 
            target_folder, 
            json_folder, 
            predict_folder, 
            filename, 
            file_id, 
            repo_id,
            task_id
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
            shutil.rmtree(work_dir)
            logger.info(f"[Task {task_id}] Cleaned up work directory")
        except Exception as e:
            logger.warning(f"[Task {task_id}] Failed to clean up work directory: {str(e)}")
        
    except Exception as e:
        # 异常处理：记录错误并更新任务状态
        logger.error(f"[Task {task_id}] Error in background processing: {str(e)}")
        task_status[task_id] = f"error: {str(e)}"
        
        # 尝试更新文件状态为错误
        try:
            await asyncio.to_thread(update_file_status, repo_id, file_id, f"error: {str(e)}", True)
        except Exception as update_error:
            logger.error(f"[Task {task_id}] Failed to update file status: {str(update_error)}")

# ===== 文件处理核心逻辑 =====
def process_data(work_dir, upload_folder, target_folder, json_folder, predict_folder, 
                filename, file_id, repo_id, task_id):
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
        work_dir (str): 工作目录路径
        upload_folder (str): 源文件目录
        target_folder (str): 目标文件目录
        json_folder (str): JSON输出目录
        predict_folder (str): 预测数据目录
        filename (str): 文件名
        file_id (str): 文件ID
        repo_id (str): 仓库ID
        task_id (str): 任务ID
        
    返回:
        tuple: (JSON结果数据, 预测结果)
    """
    try:
        logger.info(f"[Task {task_id}] Starting data processing in separate process")
        
        # 第一步：结构化处理
        # 将原始文件转换为结构化格式
        logger.info(f"[Task {task_id}] Step 1: Data structuring")
        try:
            # 保存原始工作目录
            original_cwd = os.getcwd()
            
            # 更改工作目录到工作区根目录
            # 这是因为一些处理脚本可能使用相对路径
            os.chdir(work_dir)
            
            # 创建子任务ID，用于多阶段处理
            subtask_id = f"{task_id}_structuring"
            
            # 在子进程中执行数据结构化处理
            # 【注意】为何嵌套多进程：
            # 主进程池已经创建了工作进程，但有些处理可能需要进一步并行
            # 这种模式允许更精细的并行控制
            with ProcessPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    process_subtask,
                    upload_folder,
                    target_folder,
                    json_folder,
                    predict_folder,
                    subtask_id
                )
                # 等待子任务完成
                future.result(timeout=300)  # 设置5分钟超时
            
            # 恢复原始工作目录
            os.chdir(original_cwd)
            
            logger.info(f"[Task {task_id}] Data structuring completed")
            
        except concurrent.futures.TimeoutError:
            # 超时处理：记录错误并返回失败结果
            logger.error(f"[Task {task_id}] Data structuring timed out after 5 minutes")
            update_file_status(repo_id, file_id, "error: processing timeout", True)
            return None, None
            
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
            
            # 预测所有文件的风险
            predictions = predict_all(source_folder=predict_folder)
            
            logger.info(f"[Task {task_id}] Risk prediction completed: {predictions}")
            
            # 获取该文件的预测结果
            excel_name = os.path.splitext(filename)[0] + ".xlsx"
            prediction_result = predictions.get(f'{excel_name}', None)
            
            # 更新文件状态为预测结果
            # 如果有预测结果，将其作为状态；否则使用通用完成状态
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
        
        # 转换目标数据到JSON
        target_to_json.process_target_to_json(target_folder=target_folder, json_folder=json_folder)
        
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
                
            except Exception as e:
                # 解析单个JSON文件失败不应阻止整个处理流程
                logger.error(f"[Task {task_id}] Error parsing JSON file {json_file}: {str(e)}")
                all_json_content[os.path.basename(json_file)] = {"error": str(e)}
        
        # 第四步：保存处理结果到数据库
        logger.info(f"[Task {task_id}] Step 4: Saving results to database")
        
        # 生成完整的JSON结果
        json_result = {
            "content": all_json_content,
            "predictions": predictions
        }
        
        # 更新数据库中的JSON结果
        create_or_update_json_res(file_id, json_result)
        
        # 上传处理结果文件到GridFS
        # 找到生成的Excel文件
        excel_files = glob.glob(os.path.join(target_folder, "*.xlsx"))
        for excel_file in excel_files:
            try:
                # 读取Excel文件内容
                with open(excel_file, "rb") as f:
                    excel_content = f.read()
                
                # 上传结果文件
                excel_filename = os.path.basename(excel_file)
                upload_res_file(
                    repo_id=repo_id,
                    file_content=excel_content,
                    filename=excel_filename,
                    source_file=file_id
                )
                
                logger.info(f"[Task {task_id}] Uploaded result file: {excel_filename}")
                
            except Exception as e:
                # 上传结果文件失败不应阻止整个处理流程
                logger.error(f"[Task {task_id}] Failed to upload result file {excel_file}: {str(e)}")
        
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
        logger.info(f"[Subtask {subtask_id}] Starting in separate process")
        
        # 清理可能存在的旧文件
        cleanup_work_dir(upload_folder, target_folder, json_folder, predict_folder)
        
        # 确保目录存在
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(target_folder, exist_ok=True)
        os.makedirs(json_folder, exist_ok=True)
        os.makedirs(predict_folder, exist_ok=True)
        
        # 执行主处理逻辑
        # main_process是数据结构化模块的入口点
        main_process.main_process(
            source_dir=upload_folder,
            target_dir=target_folder
        )
        
        # 如果目标目录中有文件，则处理成功
        target_files = glob.glob(os.path.join(target_folder, "*"))
        success = len(target_files) > 0
        
        logger.info(f"[Subtask {subtask_id}] Completed {'successfully' if success else 'with errors'}")
        return success
        
    except Exception as e:
        # 异常处理：记录错误并返回失败结果
        logger.error(f"[Subtask {subtask_id}] Error: {str(e)}")
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