from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from io import BytesIO

# 假设这些函数是从 db_util.py 中导入
from db.db_util import (
    upload_file,
    get_file_metadata_by_id,
    delete_file,
    download_file,
    update_file_status
)

from models._file import FileMetadata

router = APIRouter()

@router.post("/upload", response_model=FileMetadata)
async def upload_file_api(repo_id: str, 
                          cur_file: UploadFile = File(...), 
                          source: bool = True):
    """
    上传文件到 GridFS，并更新指定 repo_id 对应的 files 或 results 列表。
    - source=True 表示更新 repo.files
    - source=False 表示更新 repo.results
    """
    # 将上传的文件内容读取到内存
    file_content = await cur_file.read()

    file_id = upload_file(
        repo_id=repo_id,
        file_obj=BytesIO(file_content),  # 用 BytesIO 包装一下
        filename= cur_file.filename,
        source=source
    )
    print(file_id)

    if not file_id:
        raise HTTPException(status_code=400, detail="File upload failed")

    # 获取上传后该文件的元数据返回
    metadata = get_file_metadata_by_id(repo_id, file_id, source)
    if not metadata:
        raise HTTPException(status_code=404, detail="File metadata not found")
    
    return metadata


@router.get("/{file_id}", response_model=FileMetadata)
async def get_file_metadata_api(repo_id: str, file_id: str, source: bool = True):
    """
    获取指定 file_id 的文件元数据。
    - source=True 表示从 repo.files 获取
    - source=False 表示从 repo.results 获取
    """
    metadata = get_file_metadata_by_id(repo_id, file_id, source)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    return metadata


@router.delete("/{file_id}")
async def delete_file_api(file_id: str):
    """
    删除指定 file_id 的文件，并从所有 repo.files 或 repo.results 中移除该文件记录
    """
    result = delete_file(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found or already deleted")
    return {"detail": "File deleted successfully"}


@router.get("/{file_id}/download")
async def download_file_api(file_id: str):
    """
    下载指定 file_id 的文件内容，返回一个流式响应。
    """
    file_data = download_file(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    filename, file_content = file_data
    # 使用 BytesIO 进行包装并返回流式响应
    file_like = BytesIO(file_content)
    file_like.seek(0)

    # 以 StreamingResponse 形式返回
    return StreamingResponse(
        file_like,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.put("/{file_id}", response_model=str)
async def update_file_status_api(repo_id: str, 
                                 file_id: str, 
                                 new_status: str = "complete", 
                                 source: bool = True):
    """
    更新文件状态，例如将 status 字段设置为 "complete" 或其它。
    - source=True 表示更新 repo.files
    - source=False 表示更新 repo.results
    """
    result = update_file_status(repo_id, file_id, new_status, source)
    if result == "not found":
        raise HTTPException(status_code=404, detail="File not found")
    return f"File {file_id} status updated to {new_status}"
