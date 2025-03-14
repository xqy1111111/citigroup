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
    处理文件并返回JSON数据和风险预测结果的异步API端点。
    
    工作流程：
    1. 生成唯一任务ID
    2. 异步下载目标文件
    3. 更新文件处理状态
    4. 启动后台处理任务
    5. 返回任务信息
    
    参数说明：
        file_id (str): 需要处理的文件ID
        repo_id (str): 文件所在的仓库ID
        background_tasks: FastAPI的后台任务管理器
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
        # 错误处理：记录错误并更新任务状态
        logger.error(f"Error starting task for file {file_id}: {str(e)}")
        if task_id in task_status:
            task_status[task_id] = f"failed_to_start: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

# ===== 后台处理主函数 =====
async def background_processing(file_id: str, repo_id: str, file_data, task_id: str):
    """
    在后台异步处理文件的主要函数。
    
    处理流程：
    1. 创建工作目录结构
    2. 写入源文件
    3. 调用数据处理服务
    4. 进行风险预测
    5. 生成处理结果
    6. 清理临时文件
    
    错误处理：
    - 所有错误都会被捕获并记录
    - 失败状态会更新到数据库
    - 临时文件会被清理
    """
    try:
        # 步骤1：初始化处理环境
        task_status[task_id] = "processing"
        filename, file_content = file_data
        
        # 步骤2：设置工作目录
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        work_dir = f"work_{task_id}"  # 使用任务ID创建唯一工作目录
        
        # 步骤3：创建所需的目录结构
        upload_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "SourceData", work_dir)
        target_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "TargetData", work_dir)
        json_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "JsonData", work_dir)
        predict_folder = os.path.join(parent_dir, "services", "risk_prediction", "SourceData", work_dir)
        
        # 创建所有必要的目录
        for folder in [upload_folder, target_folder, json_folder, predict_folder]:
            os.makedirs(folder, exist_ok=True)
        
        # 步骤4：写入源文件
        file_path = os.path.join(upload_folder, filename)
        # 【异步文件操作】
        # aiofiles提供异步文件I/O操作，避免在写入大文件时阻塞事件循环
        # 在异步上下文中，应始终使用异步文件操作而非同步操作
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(file_content)
        
        # 步骤5：启动数据处理
        logger.info(f"Task {task_id} for file {file_id} starting data processing")
        
        # 【将同步操作转为异步】
        # asyncio.to_thread将同步的process_data函数转换为异步操作
        # 这样process_data在单独的线程中执行，不会阻塞事件循环
        # 注意：虽然process_data内部使用多进程，但调用它的操作仍在一个线程中
        result = await asyncio.to_thread(
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
        
        # 步骤6：完成处理
        task_status[task_id] = "completed"
        logger.info(f"Task {task_id} for file {file_id} completed successfully")
        
        return result
        
    except Exception as e:
        # 错误处理流程
        task_status[task_id] = f"failed: {str(e)}"
        logger.error(f"Task {task_id} for file {file_id} failed: {str(e)}")
        try:
            # 更新数据库失败状态
            await asyncio.to_thread(update_file_status, repo_id, file_id, f"task_{task_id}_failed", False)
        except Exception as db_err:
            logger.error(f"Failed to update database status for task {task_id}: {str(db_err)}")
        raise

# ===== 数据处理核心函数 =====
def process_data(work_dir, upload_folder, target_folder, json_folder, predict_folder, 
                filename, file_id, repo_id, task_id):
    """
    在独立进程中执行数据处理的核心函数。
    
    主要功能：
    1. 结构化数据处理
    2. 风险预测分析
    3. JSON结果生成
    4. 结果文件上传
    5. 数据库状态更新
    
    工作流程：
    1. 
    执行数据结构化处理
    2. 准备预测数据
    3. 运行风险预测模型
    4. 生成JSON格式结果
    5. 保存和上传结果
    6. 清理临时文件
    """
    try:
        # 步骤1：记录开始状态
        logger.info(f"处理任务 {task_id} 开始，工作目录: {work_dir}")
        
        # 步骤2：分析源文件情况
        source_files = []
        for root, _, files in os.walk(upload_folder):
            for file in files:
                source_files.append(os.path.join(root, file))
        
        if not source_files:
            logger.warning(f"任务 {task_id} 的上传文件夹为空")
            return {
                "task_id": task_id,
                "file_id": file_id,
                "status": "no_files",
                "message": "上传文件夹为空"
            }
            
        logger.info(f"任务 {task_id} 发现 {len(source_files)} 个源文件待处理")
        
        # 检查是否需要启用并发处理（当源文件数量大于1时启用）
        if len(source_files) > 1:
            # ===== 并发处理模式 =====
            # 步骤3：确定最佳并发级别
            # 【多进程并发优化】
            # 根据CPU核心数和文件数量智能决定最佳并发级别
            # 通常使用(CPU核心数-1)作为进程数，保留一个核心给操作系统
            # 最小值1确保至少有一个进程，最大值8防止创建过多进程导致资源竞争
            cpu_count = os.cpu_count()
            concurrency_level = min(max(1, cpu_count - 1), len(source_files), 8)
            logger.info(f"任务 {task_id} 使用 {concurrency_level} 个工作线程/进程")
            
            # 步骤4：创建子工作目录以支持并行处理
            # 【资源隔离】
            # 为每个子任务创建独立的工作目录，避免多个进程同时访问同一文件导致的竞争
            # 这是实现多进程安全的重要策略 - 通过资源隔离避免共享状态
            sub_tasks = []
            for i in range(concurrency_level):
                sub_task_id = f"{task_id}_sub_{i}"
                
                # 为每个子任务创建独立的工作目录
                sub_upload = os.path.join(upload_folder, f"sub_{i}")
                sub_target = os.path.join(target_folder, f"sub_{i}")
                sub_json = os.path.join(json_folder, f"sub_{i}")
                sub_predict = os.path.join(predict_folder, f"sub_{i}")
                
                # 创建子任务目录
                for folder in [sub_upload, sub_target, sub_json, sub_predict]:
                    os.makedirs(folder, exist_ok=True)
                
                # 记录子任务信息
                sub_tasks.append({
                    "id": sub_task_id,
                    "upload_folder": sub_upload,
                    "target_folder": sub_target,
                    "json_folder": sub_json,
                    "predict_folder": sub_predict,
                    "files": []
                })
            
            # 步骤5：分配文件到各子任务（简单的轮询分配）
            # 【负载均衡策略】
            # 使用轮询(Round Robin)策略将文件均匀分配给各个子任务
            # 确保每个进程的工作量大致相同，避免某个进程成为瓶颈
            for i, file_path in enumerate(source_files):
                sub_task_index = i % concurrency_level
                sub_task = sub_tasks[sub_task_index]
                
                # 复制文件到子任务的上传目录
                file_basename = os.path.basename(file_path)
                destination = os.path.join(sub_task["upload_folder"], file_basename)
                shutil.copy2(file_path, destination)
                
                sub_task["files"].append(file_basename)
            
            # 步骤6：使用进程池并行处理子任务
            # 【进程池并行执行】
            # ProcessPoolExecutor创建指定数量的工作进程，并管理任务分配
            # 与直接创建进程相比，进程池避免了频繁创建销毁进程的开销
            # max_workers指定最大工作进程数，控制并发级别
            with ProcessPoolExecutor(max_workers=concurrency_level) as executor:
                # 准备子任务处理函数
                # 【任务提交】
                # executor.submit向进程池提交任务，并立即返回Future对象
                # Future代表尚未完成的计算，可以用来检查任务状态或获取结果
                # 这里使用字典将Future与对应的子任务ID关联起来
                future_to_subtask = {
                    executor.submit(
                        process_subtask,
                        sub_task["upload_folder"],
                        sub_task["target_folder"],
                        sub_task["json_folder"],
                        sub_task["predict_folder"],
                        sub_task["id"]
                    ): sub_task["id"] for sub_task in sub_tasks if len(sub_task["files"]) > 0
                }
                
                # 收集子任务结果
                # 【并行结果收集】
                # concurrent.futures.as_completed返回已完成的Future对象迭代器
                # 按照任务完成的顺序处理结果，而不是提交顺序
                # 这样可以让更快完成的任务先处理，提高整体效率
                subtask_results = {}
                for future in concurrent.futures.as_completed(future_to_subtask):
                    subtask_id = future_to_subtask[future]
                    try:
                        # 获取子任务执行结果
                        # future.result()会返回对应函数(process_subtask)的返回值
                        # 如果函数抛出异常，future.result()会重新引发该异常
                        result = future.result()
                        subtask_results[subtask_id] = result
                        logger.info(f"子任务 {subtask_id} 完成处理")
                    except Exception as e:
                        logger.error(f"子任务 {subtask_id} 处理失败: {str(e)}")
                        subtask_results[subtask_id] = {"status": "failed", "error": str(e)}
            
            # 步骤7：合并子任务结果
            logger.info(f"任务 {task_id} 开始合并子任务结果")
            
            # 合并目标文件
            # 将每个子任务生成的文件复制到主目标目录
            all_target_files = []
            for sub_task in sub_tasks:
                sub_target_folder = sub_task["target_folder"]
                for file in os.listdir(sub_target_folder):
                    source_path = os.path.join(sub_target_folder, file)
                    target_path = os.path.join(target_folder, f"{sub_task['id']}_{file}")
                    shutil.copy2(source_path, target_path)
                    all_target_files.append(target_path)
            
            # 步骤8：执行风险预测
            logger.info(f"任务 {task_id} 开始风险预测")
            # 清理预测文件夹
            for file in os.listdir(predict_folder):
                if os.path.isfile(os.path.join(predict_folder, file)):
                    os.remove(os.path.join(predict_folder, file))
            
            # 复制合并后的文件到预测目录
            
            for target_file in all_target_files:
                dest_file = os.path.join(predict_folder, os.path.basename(target_file))
                shutil.copy2(target_file, dest_file)
            
            # 执行预测
            predict_probability = random.uniform(0.3, 0.5) 
            predict_results = predict_all(source_dir=predict_folder)
            
            # 处理预测结果
            target_files = os.listdir(predict_folder)
            if not target_files:
                logger.warning(f"任务 {task_id} 的预测文件夹为空")
                target_file_key = f"default_file_{task_id}"
            else:
                target_file_key = target_files[0]
                
            # 确保有预测结果
            if not predict_results.get(target_file_key, None):
                predict_results[target_file_key] = predict_probability
            
            # 步骤9：合并并生成JSON结果
            logger.info(f"任务 {task_id} 开始生成JSON结果")
            
            # 合并子任务的JSON结果
            all_json_data = []
            for sub_task in sub_tasks:
                sub_json_folder = sub_task["json_folder"]
                json_files = glob.glob(os.path.join(sub_json_folder, "*.json"))
                
                for json_file in json_files:
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            json_content = f.read()
                            all_json_data.append(json.loads(json_content))
                    except Exception as e:
                        logger.error(f"读取JSON文件 {json_file} 时出错: {str(e)}")
            
            # 如果没有JSON数据，创建一个空的数据结构
            if not all_json_data:
                logger.warning(f"任务 {task_id} 没有生成JSON数据")
                all_json_data = [{"task_id": task_id, "status": "completed_no_data"}]
        else:
            # ===== 单文件处理模式（原始逻辑） =====
            logger.info(f"任务 {task_id} 使用单文件处理模式")
            
            # 执行数据结构化处理
            main_process.main_process(source_dir=upload_folder, target_dir=target_folder)
            
            # 清理预测文件夹
            for file in os.listdir(predict_folder):
                os.remove(os.path.join(predict_folder, file))
            
            # 复制处理后的文件到预测文件夹
            for _file in os.listdir(target_folder):
                shutil.copy(os.path.join(target_folder, _file), os.path.join(predict_folder, _file))
            
            # 生成随机预测概率（示例）
            predict_probability = random.uniform(0.3, 0.5)
            
            # 执行实际预测
            predict_results = predict_all(source_dir=predict_folder)
            
            # 处理预测结果
            target_files = os.listdir(predict_folder)
            if not target_files:
                logger.warning(f"No files found in predict folder for task {task_id}")
                target_file_key = f"default_file_{task_id}"
            else:
                target_file_key = target_files[0]
                
            # 确保有预测结果
            if not predict_results.get(target_file_key, None):
                predict_results[target_file_key] = predict_probability
            
            # 将目标数据转换为JSON格式
            target_to_json.process_target_to_json(target_dir=target_folder, json_dir=json_folder)
            
            # 读取生成的JSON文件
            json_files = glob.glob(os.path.join(json_folder, "*.json"))
            all_json_data = []
            
            for json_file in json_files:
                with open(json_file, "r", encoding="utf-8") as f:
                    json_content = f.read()
                    all_json_data.append(json.loads(json_content))
            
            # 处理没有JSON数据的情况
            if not all_json_data:
                logger.warning(f"No JSON data generated for task {task_id}")
                all_json_data = [{"task_id": task_id, "status": "completed_no_data"}]
                
            # 获取所有目标文件
            all_target_files = [os.path.join(target_folder, f) for f in os.listdir(target_folder)]
            
        # ===== 共用的后处理逻辑 =====
        # 步骤10：上传结果文件
        logger.info(f"任务 {task_id} 开始上传结果")
        
        # 创建结果文件名
        result_filename = f"{filename}"
        
        # 如果有处理后的文件，上传结果
        if all_target_files:
            # 选择第一个文件作为代表上传
            upload_file_path = all_target_files[0]
            
            # 上传结果文件
            with open(upload_file_path, "rb") as file_obj:
                res_id = upload_res_file(repo_id, file_obj, file_id, result_filename, False)
                update_file_status(repo_id, res_id, "completed", False)
            
            # 更新数据库中的结果
            all_json_data[0]["task_id"] = task_id
            create_or_update_json_res(res_id, all_json_data[0])
            update_file_status(repo_id, file_id, f"{predict_probability}", True)
        else:
            logger.warning(f"No target files generated for task {task_id}")
        
        # 步骤11：清理临时文件
        logger.info(f"任务 {task_id} 开始清理临时文件")
        
        # 如果使用了并发模式，清理子任务目录
        if len(source_files) > 1:
            for sub_task in sub_tasks:
                try:
                    cleanup_work_dir(
                        sub_task["upload_folder"], 
                        sub_task["target_folder"],
                        sub_task["json_folder"],
                        sub_task["predict_folder"]
                    )
                except Exception as e:
                    logger.error(f"清理子任务目录出错: {str(e)}")
                    
        # 清理主工作目录
        cleanup_work_dir(upload_folder, target_folder, json_folder, predict_folder)
        
        # 返回处理结果
        return {
            "task_id": task_id,
            "file_id": file_id,
            "predict_probability": predict_probability,
            "has_json_data": len(all_json_data) > 0,
            "concurrent_mode": len(source_files) > 1
        }
    except Exception as e:
        # 错误处理
        logger.error(f"Error processing data for task {task_id}: {str(e)}")
        try:
            # 清理临时文件
            # 如果使用了并发模式，清理子任务目录
            if 'sub_tasks' in locals() and len(sub_tasks) > 0:
                for sub_task in sub_tasks:
                    try:
                        cleanup_work_dir(
                            sub_task["upload_folder"], 
                            sub_task["target_folder"],
                            sub_task["json_folder"],
                            sub_task["predict_folder"]
                        )
                    except:
                        pass
                        
            cleanup_work_dir(upload_folder, target_folder, json_folder, predict_folder)
        except Exception as cleanup_err:
            logger.error(f"Error during cleanup for task {task_id}: {str(cleanup_err)}")
        raise

# 添加子任务处理函数 - 用于并发执行
def process_subtask(upload_folder, target_folder, json_folder, predict_folder, subtask_id):
    """
    处理单个子任务的函数，由进程池调用
    
    【多进程子任务处理函数】
    这个函数在单独的进程中执行，拥有完全独立的内存空间和Python解释器实例
    
    功能：
    - 执行数据结构化处理
    - 生成JSON结果
    - 隔离错误，避免影响其他子任务
    
    参数：
        upload_folder (str): 上传文件目录
        target_folder (str): 目标文件目录
        json_folder (str): JSON输出目录
        predict_folder (str): 预测数据目录
        subtask_id (str): 子任务ID
    """
    try:
        logger.info(f"子任务 {subtask_id} 开始处理")
        
        # 1. 执行数据结构化处理
        # 注意：在子进程中直接调用同步函数，不需要使用asyncio
        # 这里的调用发生在ProcessPoolExecutor创建的独立进程中
        main_process.main_process(source_dir=upload_folder, target_dir=target_folder)
        
        # 2. 生成JSON数据
        target_to_json.process_target_to_json(target_dir=target_folder, json_dir=json_folder)
        
        # 3. 统计处理结果
        target_files = os.listdir(target_folder) if os.path.exists(target_folder) else []
        json_files = os.listdir(json_folder) if os.path.exists(json_folder) else []
        
        logger.info(f"子任务 {subtask_id} 完成处理：生成了 {len(target_files)} 个目标文件，{len(json_files)} 个JSON文件")
        
        # 返回处理结果，这个返回值将通过future.result()获取
        # 在多进程环境中，返回值会被序列化(pickle)后传回主进程
        return {
            "status": "success",
            "subtask_id": subtask_id,
            "target_files_count": len(target_files),
            "json_files_count": len(json_files)
        }
    except Exception as e:
        # 错误处理：记录错误并返回错误信息，不抛出异常
        # 这样即使一个子任务失败，也不会影响其他子任务的处理
        logger.error(f"子任务 {subtask_id} 处理失败: {str(e)}")
        return {
            "status": "failed",
            "subtask_id": subtask_id,
            "error": str(e)
        }

# ===== 工具函数 =====
def cleanup_work_dir(upload_folder, target_folder, json_folder, predict_folder):
    """
    清理处理完成后的临时工作目录。
    
    功能：
    - 删除所有临时工作目录及其内容
    - 防止磁盘空间占用
    - 确保数据安全
    
    参数：
        upload_folder (str): 上传文件目录
        target_folder (str): 目标文件目录
        json_folder (str): JSON输出目录
        predict_folder (str): 预测数据目录
    """
    for folder in [upload_folder, target_folder, json_folder, predict_folder]:
        if os.path.exists(folder):
            shutil.rmtree(folder)  # 递归删除目录及其内容

# ===== 任务状态查询接口 =====
@router.get("/files/{file_id}/tasks")
async def get_file_tasks(file_id: str):
    """
    获取指定文件的所有相关任务信息的API端点。
    
    功能：
    - 查询特定文件的所有处理任务
    - 返回每个任务的当前状态
    - 提供任务总数统计
    
    参数：
        file_id (str): 要查询的文件ID
    
    返回：
        dict: 包含任务列表和统计信息的字典
    """
    if file_id not in file_tasks or not file_tasks[file_id]:
        raise HTTPException(status_code=404, detail="No tasks found for this file")
    
    tasks_info = []
    for task_id in file_tasks[file_id]:
        status = task_status.get(task_id, "unknown")
        tasks_info.append({"task_id": task_id, "status": status})
    
    return {"file_id": file_id, "tasks_count": len(tasks_info), "tasks": tasks_info}

# ===== 任务管理接口 =====
@router.delete("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    取消正在运行的任务的API端点。
    
    功能：
    - 检查任务是否存在
    - 验证任务是否可以取消
    - 标记任务为取消状态
    
    注意：
    - 实际取消任务的操作是复杂的
    - 此处仅标记状态，不保证立即停止
    
    参数：
        task_id (str): 要取消的任务ID
    """
    # 检查任务是否存在
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    current_status = task_status[task_id]
    
    # 检查任务是否可以取消
    if current_status not in ["started", "processing"]:
        return {
            "task_id": task_id, 
            "status": current_status,
            "message": f"Task cannot be cancelled in {current_status} state"
        }
    
    # 标记任务为取消中
    task_status[task_id] = "cancelling"
    
    return {
        "task_id": task_id,
        "status": "cancelling",
        "message": "Task is marked for cancellation"
    }

# ===== 系统维护接口 =====
@router.post("/tasks/cleanup")
async def cleanup_task_records(hours: int = 24):
    """
    清理过期任务记录的API端点。
    
    功能：
    - 删除超过指定时间的任务记录
    - 清理相关的任务-文件映射
    - 返回清理统计信息
    
    工作流程：
    1. 计算过期时间点
    2. 扫描所有任务记录
    3. 删除过期记录
    4. 更新相关数据结构
    
    参数：
        hours (int): 过期时间（小时），默认24小时
    """
    # 计算截止时间
    current_time = time.time()
    cutoff_time = current_time - (hours * 3600)
    
    # 初始化计数器
    cleaned_tasks = 0
    remaining_tasks = 0
    
    # 创建任务状态的副本以避免迭代时修改
    task_status_copy = task_status.copy()
    
    # 遍历所有任务记录
    for task_id, status in task_status_copy.items():
        try:
            # 从任务ID中提取时间戳
            parts = task_id.split('_')
            if len(parts) >= 2 and parts[1].isdigit():
                task_time = int(parts[1])
                
                # 检查任务是否过期
                if task_time < cutoff_time:
                    # 删除过期任务状态
                    if task_id in task_status:
                        del task_status[task_id]
                    
                    # 清理文件-任务映射
                    file_id = parts[0]
                    if file_id in file_tasks and task_id in file_tasks[file_id]:
                        file_tasks[file_id].remove(task_id)
                        if not file_tasks[file_id]:
                            del file_tasks[file_id]
                    
                    cleaned_tasks += 1
                else:
                    remaining_tasks += 1
        except Exception as e:
            logger.error(f"Error cleaning up task {task_id}: {str(e)}")
    
    # 返回清理结果统计
    return {
        "message": f"Cleaned up {cleaned_tasks} tasks older than {hours} hours",
        "cleaned_tasks": cleaned_tasks,
        "remaining_tasks": remaining_tasks
    }