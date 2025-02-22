from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from models._file import FileUpload, FileMetadata, FileStatusUpdate
from db.db_util import upload_file, get_file_metadata_by_id, delete_file, download_file, update_file_status

router = APIRouter()

# 文件上传
@router.post("/upload/", response_model=str)
async def upload_new_file(file_info: FileUpload, file: UploadFile file(...)):
    file_id = upload_file(file.repo_id, file.file_obj, file.filename, file.source)
    if not file_id:
        raise HTTPException(status_code=400, detail="Failed to upload file")
    return file_id

# 获取文件元数据
@router.get("/{repo_id}/{file_id}", response_model=FileMetadata)
async def get_file_metadata(repo_id: str, file_id: str, source: bool = True):
    file_metadata = get_file_metadata_by_id(repo_id, file_id, source)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    return file_metadata

# 删除文件
@router.delete("/{file_id}", response_model=str)
async def delete_existing_file(file_id: str):
    status = delete_file(file_id)
    if status == "success":
        return "File deleted successfully"
    raise HTTPException(status_code=400, detail="Failed to delete file")

# 下载文件
@router.get("/{file_id}/download/")
async def download_existing_file(file_id: str):
    filename, file_content = download_file(file_id)
    if not file_content:
        raise HTTPException(status_code=404, detail="File not found")
    return {"filename": filename, "file_content": file_content}

# 更新文件状态
@router.put("/{repo_id}/{file_id}/status", response_model=str)
async def update_file_status_for_repo(repo_id: str, file_id: str, status_update: FileStatusUpdate):
    status = update_file_status(repo_id, file_id, status_update.status, status_update.source)
    if status == "success":
        return f"File status updated to {status_update.status}"
    raise HTTPException(status_code=400, detail="Failed to update file status")
