"""
文件管理API路由模块

这个模块实现了与文件管理相关的所有API端点，包括：
1. 文件上传 - 将用户文件保存到GridFS和仓库中
2. 文件下载 - 从系统中检索和流式传输文件
3. 文件元数据获取 - 查询文件的详细信息
4. 文件删除 - 移除文件及其相关记录
5. 文件状态更新 - 更新处理状态和结果

文件管理是系统的基础功能，支持用户上传金融文档、获取处理结果和管理文件资源。
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from io import BytesIO
import urllib.parse

# 从数据库工具模块导入文件操作函数
from db.db_util import (
    upload_source_file,
    get_file_metadata_by_id,
    delete_file,
    download_file,
    update_file_status,
    get_json_res
)

from models._file import FileMetadata, JsonRes

# 创建路由器实例
router = APIRouter()

@router.post("/upload", response_model=FileMetadata)
async def upload_file_api(repo_id: str, 
                          cur_file: UploadFile = File(...), 
                          source: bool = True):
    """
    文件上传API
    
    详细说明:
    此端点接收用户上传的文件，将其保存到MongoDB的GridFS中，
    并更新对应仓库的文件列表信息。支持上传源文件或结果文件。
    
    流程:
    1. 接收仓库ID、文件对象和文件类型标志
    2. 读取上传的文件内容到内存
    3. 调用数据库函数存储文件内容和更新仓库记录
    4. 获取并返回文件元数据
    
    参数:
        repo_id (str): 仓库的唯一标识符
        cur_file (UploadFile): 用户上传的文件对象
        source (bool): 文件类型标志
                     - True表示源文件(保存到repo.files)
                     - False表示结果文件(保存到repo.results)
        
    返回:
        FileMetadata: 上传文件的元数据信息
        
    错误:
        400 Bad Request - 文件上传失败
        404 Not Found - 文件元数据未找到
    """
    # 将上传的文件内容读取到内存
    file_content = await cur_file.read()

    # 调用数据库工具函数存储文件并获取文件ID
    file_id = upload_source_file(
        repo_id=repo_id,
        file_obj=BytesIO(file_content),  # 用BytesIO包装文件内容
        filename= cur_file.filename,
        source=source
    )
    print(file_id)  # 调试输出文件ID

    # 检查文件上传是否成功
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
    获取文件元数据API
    
    详细说明:
    此端点根据文件ID和仓库ID获取文件的元数据信息，
    包括文件名、大小、上传时间、状态等。
    
    流程:
    1. 接收仓库ID、文件ID和文件类型标志
    2. 调用数据库函数获取文件元数据
    3. 返回文件元数据对象
    
    参数:
        repo_id (str): 仓库的唯一标识符
        file_id (str): 文件的唯一标识符
        source (bool): 文件类型标志
                     - True表示源文件(从repo.files查询)
                     - False表示结果文件(从repo.results查询)
        
    返回:
        FileMetadata: 文件的元数据信息
        
    错误:
        404 Not Found - 指定文件不存在
    """
    # 调用数据库工具函数获取文件元数据
    metadata = get_file_metadata_by_id(repo_id, file_id, source)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    return metadata


@router.delete("/{file_id}")
async def delete_file_api(file_id: str):
    """
    删除文件API
    
    详细说明:
    此端点根据文件ID删除GridFS中的文件，并从所有引用该文件的仓库记录中
    移除相关的文件记录。这是一个不可逆操作。
    
    流程:
    1. 接收文件ID
    2. 调用数据库函数删除文件和相关记录
    3. 返回删除操作结果
    
    参数:
        file_id (str): 要删除的文件的唯一标识符
        
    返回:
        dict: 包含删除操作结果的消息
        
    错误:
        404 Not Found - 文件不存在或已被删除
    """
    # 调用数据库工具函数删除文件
    result = delete_file(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found or already deleted")
    return {"detail": "File deleted successfully"}


@router.get("/{file_id}/download")
async def download_file_api(file_id: str):
    """
    文件下载API
    
    详细说明:
    此端点根据文件ID从GridFS中检索文件内容，并以流式响应方式
    提供文件下载。支持各种文件类型，并处理文件名编码以确保兼容性。
    
    流程:
    1. 接收文件ID
    2. 调用数据库函数获取文件内容和文件名
    3. 创建BytesIO对象包装文件内容
    4. 设置适当的响应头并返回流式响应
    
    参数:
        file_id (str): 要下载的文件的唯一标识符
        
    返回:
        StreamingResponse: 文件内容的流式传输响应
        
    错误:
        404 Not Found - 文件不存在
    """
    # 调用数据库工具函数获取文件数据
    file_data = download_file(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    # 解包文件名和文件内容
    filename, file_content = file_data
    # 创建内存流对象
    file_like = BytesIO(file_content)
    file_like.seek(0)  # 将指针设置到流的开始位置

    # 处理文件名，防止编码问题
    encoded_filename = urllib.parse.quote(filename)  # 处理非ASCII文件名

    # 返回流式响应
    return StreamingResponse(
        file_like,
        media_type="application/octet-stream",  # 通用二进制数据类型
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"  # 设置下载文件名
        }
    )

@router.put("/{file_id}", response_model=str)
async def update_file_status_api(repo_id: str, 
                                 file_id: str, 
                                 new_status: str = "complete", 
                                 source: bool = True):
    """
    更新文件状态API
    
    详细说明:
    此端点用于更新文件的处理状态。例如，当文件处理完成时，
    可以将状态从"uploaded"更新为"complete"或其他值。
    
    流程:
    1. 接收仓库ID、文件ID、新状态和文件类型标志
    2. 调用数据库函数更新文件状态
    3. 返回更新结果
    
    参数:
        repo_id (str): 仓库的唯一标识符
        file_id (str): 文件的唯一标识符
        new_status (str): 新的文件状态值，默认为"complete"
        source (bool): 文件类型标志
                     - True表示源文件(更新repo.files)
                     - False表示结果文件(更新repo.results)
        
    返回:
        str: 更新操作结果的消息
        
    错误:
        404 Not Found - 文件不存在
    """
    # 调用数据库工具函数更新文件状态
    result = update_file_status(repo_id, file_id, new_status, source)
    if result == "not found":
        raise HTTPException(status_code=404, detail="File not found")
    return f"File {file_id} status updated to {new_status}"


@router.get("/json_res/{file_id}")
async def get_json_res_api(file_id: str):
    """
    获取文件JSON结果API
    
    详细说明:
    此端点用于获取文件处理后生成的JSON格式结果数据。
    通常用于获取经过结构化处理的文件内容、分析结果等。
    
    流程:
    1. 接收文件ID
    2. 调用数据库函数获取对应的JSON结果
    3. 返回格式化的JsonRes对象
    
    参数:
        file_id (str): 文件的唯一标识符(注意：这是源文件ID，不是JSON结果的ID)
        
    返回:
        JsonRes: 包含结果ID、文件ID和JSON内容的响应对象
        
    错误:
        404 Not Found - JSON结果不存在，可能是文件尚未处理或ID错误
    """
    # 调用数据库工具函数获取JSON结果
    json_res = get_json_res(file_id)
    if json_res == None:
        raise HTTPException(status_code=404, detail="Res not found, have you process or pass in the right file_id?")
    # 返回格式化的JsonRes对象
    return JsonRes(res_id=str(json_res.get("_id")), file_id=str(json_res.get("file_id")), content=json_res.get("content"))
