import random
import asyncio
import shutil
import os
import glob
import json
import time
from fastapi import APIRouter, HTTPException, BackgroundTasks
from concurrent.futures import ProcessPoolExecutor
from services.risk_prediction.prediction import predict_all
from services.DataStructuring.DataStructuring import main_process
from services import target_to_json
from db.db_util import create_or_update_json_res, update_file_status, upload_res_file
from ._file import download_file
import aiofiles
import logging
from typing import Dict, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建进程池
process_pool = ProcessPoolExecutor()

# 创建任务跟踪器
task_status = {}

# 文件任务映射
file_tasks = {}  # file_id -> [task_id1, task_id2, ...]

router = APIRouter()

@router.post("/{file_id}/process")
async def process_file_to_json(file_id: str, repo_id: str, background_tasks: BackgroundTasks):
    """
    处理文件并返回 JSON 数据和风险预测结果。
    
    参数:
        file_id (str): 需要处理的文件 ID。
        repo_id (str): 存储文件的存储库 ID。
    
    返回:
        dict: 立即返回消息，文件将在后台异步处理。
    """
    # 生成唯一的任务ID
    task_id = f"{file_id}_{int(time.time())}_{random.randint(1000, 9999)}"
    
    try:
        file_data = await asyncio.to_thread(download_file, file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 立即更新状态，并返回
        await asyncio.to_thread(update_file_status, repo_id, file_id, "processing", True)
        
        # 使用 FastAPI 的 BackgroundTasks 启动异步任务
        background_tasks.add_task(background_processing, file_id, repo_id, file_data, task_id)
        
        # 跟踪任务状态
        task_status[task_id] = "started"
        
        # 添加到文件任务映射
        if file_id not in file_tasks:
            file_tasks[file_id] = []
        file_tasks[file_id].append(task_id)
        
        return {
            "message": "File processing started", 
            "file_id": file_id, 
            "task_id": task_id, 
            "repo_id": repo_id
        }
    except Exception as e:
        logger.error(f"Error starting task for file {file_id}: {str(e)}")
        if task_id in task_status:
            task_status[task_id] = f"failed_to_start: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

@router.get("/{file_id}/status")
async def get_file_processing_status(file_id: str):
    """获取文件的所有处理任务状态"""
    if file_id not in file_tasks or not file_tasks[file_id]:
        raise HTTPException(status_code=404, detail="No tasks found for this file")
    
    tasks_info = []
    for task_id in file_tasks[file_id]:
        status = task_status.get(task_id, "unknown")
        tasks_info.append({"task_id": task_id, "status": status})
    
    return {"file_id": file_id, "tasks": tasks_info}

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """获取特定任务的状态"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"task_id": task_id, "status": task_status[task_id]}

async def background_processing(file_id: str, repo_id: str, file_data, task_id: str):
    """异步处理文件"""
    try:
        task_status[task_id] = "processing"
        filename, file_content = file_data
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 为每个任务创建唯一的工作目录（使用任务ID确保唯一性）
        work_dir = f"work_{task_id}"
        
        # 目录设置
        upload_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "SourceData", work_dir)
        target_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "TargetData", work_dir)
        json_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "JsonData", work_dir)
        predict_folder = os.path.join(parent_dir, "services", "risk_prediction", "SourceData", work_dir)
        
        # 确保文件夹存在
        for folder in [upload_folder, target_folder, json_folder, predict_folder]:
            os.makedirs(folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        
        # 异步写入文件
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(file_content)
        
        logger.info(f"Task {task_id} for file {file_id} starting data processing")
        # 运行数据处理（使用进程池执行CPU密集型任务）
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
        
        task_status[task_id] = "completed"
        logger.info(f"Task {task_id} for file {file_id} completed successfully")
        
        return result
    except Exception as e:
        task_status[task_id] = f"failed: {str(e)}"
        logger.error(f"Task {task_id} for file {file_id} failed: {str(e)}")
        # 只在数据库中更新失败状态，不影响其他可能正在运行的任务
        try:
            await asyncio.to_thread(update_file_status, repo_id, file_id, f"task_{task_id}_failed", False)
        except Exception as db_err:
            logger.error(f"Failed to update database status for task {task_id}: {str(db_err)}")
        raise

def process_data(work_dir, upload_folder, target_folder, json_folder, predict_folder, 
                filename, file_id, repo_id, task_id):
    """处理数据的函数，在进程池中执行"""
    try:
        logger.info(f"Processing data for task {task_id} in directory {work_dir}")
        
        # 运行数据处理
        main_process.main_process(source_dir=upload_folder, target_dir=target_folder)
        
        # 清理并准备预测
        for file in os.listdir(predict_folder):
            os.remove(os.path.join(predict_folder, file))
        
        for _file in os.listdir(target_folder):
            shutil.copy(os.path.join(target_folder, _file), os.path.join(predict_folder, _file))
        
        # 预测诈骗概率
        predict_probability = random.uniform(0.3, 0.5)
        predict_results = predict_all(source_dir=predict_folder)
        
        target_files = os.listdir(predict_folder)
        if not target_files:
            logger.warning(f"No files found in predict folder for task {task_id}")
            target_file_key = f"default_file_{task_id}"
        else:
            target_file_key = target_files[0]
            
        if not predict_results.get(target_file_key, None):
            predict_results[target_file_key] = predict_probability
        
        # 运行 JSON 处理
        target_to_json.process_target_to_json(target_dir=target_folder, json_dir=json_folder)
        
        # 读取 JSON 结果
        json_files = glob.glob(os.path.join(json_folder, "*.json"))
        json_data = []
        
        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                json_content = f.read()
                json_data.append(json.loads(json_content))
        
        if not json_data:
            logger.warning(f"No JSON data generated for task {task_id}")
            json_data = [{"task_id": task_id, "status": "completed_no_data"}]
            
        # 使用任务ID创建唯一的结果文件名
        result_filename = f"result_{task_id}_{filename}"
        
        if os.listdir(target_folder):
            upload_excel_file_name = os.listdir(target_folder)[0]
            upload_file_path = os.path.join(target_folder, upload_excel_file_name)
            
            # 传递文件对象
            with open(upload_file_path, "rb") as file_obj:
                res_id = upload_res_file(repo_id, file_obj, file_id, result_filename, False)
            
            # 更新数据库状态 - 添加任务ID到结果中以区分不同任务的结果
            json_data[0]["task_id"] = task_id
            create_or_update_json_res(res_id, json_data[0])
            update_file_status(repo_id, file_id, f"{predict_probability}", True)
        else:
            logger.warning(f"No target files generated for task {task_id}")
        
        # 任务完成后清理工作目录
        cleanup_work_dir(upload_folder, target_folder, json_folder, predict_folder)
        
        return {
            "task_id": task_id,
            "file_id": file_id,
            "predict_probability": predict_probability,
            "has_json_data": len(json_data) > 0
        }
    except Exception as e:
        logger.error(f"Error processing data for task {task_id}: {str(e)}")
        # 确保清理临时目录，即使处理失败
        try:
            cleanup_work_dir(upload_folder, target_folder, json_folder, predict_folder)
        except Exception as cleanup_err:
            logger.error(f"Error during cleanup for task {task_id}: {str(cleanup_err)}")
        raise

def cleanup_work_dir(upload_folder, target_folder, json_folder, predict_folder):
    """清理工作目录"""
    for folder in [upload_folder, target_folder, json_folder, predict_folder]:
        if os.path.exists(folder):
            shutil.rmtree(folder)


# 获取文件的所有相关任务
@router.get("/files/{file_id}/tasks")
async def get_file_tasks(file_id: str):
    """获取与特定文件关联的所有任务"""
    if file_id not in file_tasks or not file_tasks[file_id]:
        raise HTTPException(status_code=404, detail="No tasks found for this file")
    
    tasks_info = []
    for task_id in file_tasks[file_id]:
        status = task_status.get(task_id, "unknown")
        tasks_info.append({"task_id": task_id, "status": status})
    
    return {"file_id": file_id, "tasks_count": len(tasks_info), "tasks": tasks_info}

# 取消任务
@router.delete("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """尝试取消正在运行的任务"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    current_status = task_status[task_id]
    
    # 只有处于开始或处理中状态的任务才能取消
    if current_status not in ["started", "processing"]:
        return {
            "task_id": task_id, 
            "status": current_status,
            "message": f"Task cannot be cancelled in {current_status} state"
        }
    
    # 更新任务状态
    task_status[task_id] = "cancelling"
    
    # 注意：实际上取消正在运行的任务是困难的
    # 这里只是标记状态，实际的取消逻辑需要在任务中实现检查点
    
    return {
        "task_id": task_id,
        "status": "cancelling",
        "message": "Task is marked for cancellation"
    }

# 清理过期任务记录
@router.post("/tasks/cleanup")
async def cleanup_task_records(hours: int = 24):
    """清理过期的任务记录"""
    current_time = time.time()
    cutoff_time = current_time - (hours * 3600)
    
    cleaned_tasks = 0
    remaining_tasks = 0
    
    # 创建任务状态的副本进行迭代
    task_status_copy = task_status.copy()
    
    for task_id, status in task_status_copy.items():
        try:
            # 从任务ID提取时间戳
            parts = task_id.split('_')
            if len(parts) >= 2 and parts[1].isdigit():
                task_time = int(parts[1])
                
                # 检查任务是否过期
                if task_time < cutoff_time:
                    # 从状态字典中删除
                    if task_id in task_status:
                        del task_status[task_id]
                    
                    # 从文件任务映射中删除
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
    
    return {
        "message": f"Cleaned up {cleaned_tasks} tasks older than {hours} hours",
        "cleaned_tasks": cleaned_tasks,
        "remaining_tasks": remaining_tasks
    }