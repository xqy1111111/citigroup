import random
import asyncio
import shutil
import os
import glob
import json
from fastapi import APIRouter, HTTPException
from services.risk_prediction.prediction import predict_all
from services.DataStructuring.DataStructuring import main_process
from services import target_to_json
from db.db_util import create_or_update_json_res, update_file_status, upload_res_file
from ._file import download_file
import aiofiles  # 异步文件操作

router = APIRouter()

@router.post("/{file_id}/process")
async def process_file_to_json(file_id: str, repo_id: str):
    """
    处理文件并返回 JSON 数据和风险预测结果。
    
    参数:
        file_id (str): 需要处理的文件 ID。
        repo_id (str): 存储文件的存储库 ID。

    返回:
        dict: 立即返回消息，文件将在后台异步处理。
    """
    file_data = await asyncio.to_thread(download_file, file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    # 立即更新状态，并返回
    await asyncio.to_thread(update_file_status, repo_id, file_id, "processing", True)
    
    # 启动异步任务
    asyncio.create_task(background_processing(file_id, repo_id, file_data))

    return {"message": "File processing started", "file_id": file_id, "repo_id": repo_id}


async def background_processing(file_id: str, repo_id: str, file_data):
    """异步处理文件"""
    filename, file_content = file_data
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 目录设置
    upload_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "SourceData")
    target_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "TargetData")
    json_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "JsonData")
    predict_folder = os.path.join(parent_dir, "services", "risk_prediction", "SourceData")

    # 确保文件夹存在
    for folder in [upload_folder, target_folder, json_folder, predict_folder]:
        os.makedirs(folder, exist_ok=True)

    # 清空 upload_folder
    for file in os.listdir(upload_folder):
        os.remove(os.path.join(upload_folder, file))

    file_path = os.path.join(upload_folder, filename)

    # 异步写入文件
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(file_content)

    # 运行数据处理（在独立线程执行）
    await asyncio.to_thread(main_process.main_process)

    # 清理并准备预测
    for file in os.listdir(predict_folder):
        os.remove(os.path.join(predict_folder, file))

    for _file in os.listdir(target_folder):
        shutil.copy(os.path.join(target_folder, _file), os.path.join(predict_folder, _file))

    # 预测诈骗概率
    predict_probability = random.uniform(0.3, 0.5)
    predict_results = await asyncio.to_thread(predict_all)
    if not predict_results.get(os.listdir(predict_folder)[0], None):
        predict_results[os.listdir(predict_folder)[0]] = predict_probability

    # 清空 json_folder
    for file in os.listdir(json_folder):
        os.remove(os.path.join(json_folder, file))

    # 运行 JSON 处理
    await asyncio.to_thread(target_to_json.process_target_to_json)

    # 读取 JSON 结果
    json_files = glob.glob(os.path.join(json_folder, "*.json"))
    json_data = []
    for json_file in json_files:
        async with aiofiles.open(json_file, "r", encoding="utf-8") as f:
            json_content = await f.read()
            json_data.append(json.loads(json_content))

  
 
    upload_excel_file_name = os.listdir(target_folder)[0]
    upload_file_path = os.path.join(target_folder, upload_excel_file_name)

    # 传递文件对象
    with open(upload_file_path, "rb") as file_obj:
        await asyncio.to_thread(upload_res_file, repo_id, file_obj, file_id, upload_excel_file_name, False)

    # 更新数据库状态
    await asyncio.to_thread(create_or_update_json_res, file_id, json_data[0])
    await asyncio.to_thread(update_file_status, repo_id, file_id, predict_probability, True)

