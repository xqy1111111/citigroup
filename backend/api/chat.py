
import ast
from datetime import datetime
import json
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from models.chat import ChatHistory, Message


from services.ai_service import AIService
from services.DataStructuring.DataStructuring import main_process
from services import target_to_json
import shutil
import os
import platform
import glob
from services.risk_prediction.prediction import predict_all

from db.db_util import create_or_get_chat_history,update_chat_history,get_json_res,get_file_metadata_by_id,get_repo_by_id
from .repo import convert_objectid
router = APIRouter()
SYSTEM_PROMPT = """- Role: 金融风险评估专家和高级金融分析师
- Background: 用户拥有一个本地小模型，能够根据金融文件信息计算出诈骗概率。用户希望借助大模型的深度分析能力，结合诈骗概率和金融文件内容，获取关于诈骗风险的详细理由和针对性建议。
- Profile: 你是一位在金融风险评估领域经验丰富的专家，精通金融文件分析、风险识别和欺诈检测。你能够快速准确地解读金融文件的关键信息，并结合诈骗概率数据，提供全面且具有实际操作性的建议。
- Skills: 你具备金融数据分析、风险评估、欺诈检测、法律合规以及沟通能力，能够将复杂的金融信息转化为易于理解的建议。
- Goals: 
  1. 接收金融文件内容和诈骗概率数据。
  2. 分析金融文件的关键信息，结合诈骗概率数据，找出潜在的风险点。
  3. 提供详细的风险理由和针对性的建议。
- Constrains: 你的分析应基于金融文件内容和诈骗概率数据，确保建议的合理性和实用性，同时遵守金融行业的法律法规和职业道德。
- OutputFormat: 输出应包括风险理由和建议，格式清晰，便于用户理解和操作。
- Workflow:
  1. 接收金融文件内容和诈骗概率数据。
  2. 分析金融文件的关键信息，包括交易主体、资金流向、合同条款等。
  3. 结合诈骗概率数据，评估风险点并提供详细理由。
  4. 根据风险评估结果，提出针对性的建议。
- Examples:
  - 例子：
    - 金融文件内容：一份涉及跨境投资的合同，涉及金额较大，交易主体为一家新兴科技公司。
    - 诈骗概率：30%
    - 风险理由：诈骗概率较高，合同中存在一些模糊条款，资金流向不明确，且交易主体的背景信息有限。
    - 建议：建议进一步调查交易主体的背景，明确资金流向，细化合同条款，必要时咨询法律专家。
------------------------------------------------------------------------
下面是用户要求：
    """ 

ai_service = AIService()
@router.get("/")
async def get_chat(user_id: str, repo_id: str):
    """
    获取指定用户和仓库的聊天记录。

    参数:
        user_id (str): 用户的ID。
        repo_id (str): 仓库的ID。

    返回:
        ChatHistory: 聊天记录对象。
    """
    chat_history = create_or_get_chat_history(user_id, repo_id)
    
    print("\n\n\n")
    print(chat_history)
    print("\n\n\n")
    print(type(chat_history))
    
        
    chat_history = convert_objectid(chat_history)
    
    # 将 texts 中的每个对象转换为字典
    for text in chat_history["texts"]:
        print(text)
        print("\n\n\n\n\n\n")
        text["question"] = text["question"].replace('"', '\\\"')
        text["answer"] = text["answer"].replace('"', '\\\"')
        text["question"] = text["question"].replace("'", '"')
        text["answer"] = text["answer"].replace("'", '"')
        
        
        print(text["answer"])
        text["question"] = json.loads(text["question"])
        text["answer"] = json.loads(text["answer"])
    
    return chat_history


@router.post("/{user_id}/{repo_id}", response_model=Message)
async def chat(message: str, user_id: str, repo_id: str):
    """
    处理用户的聊天请求。

    参数:
        message (str): 用户发送的消息。
        user_id (str): 用户的ID。
        repo_id (str): 仓库的ID。

    返回:
        Message: 助手的响应消息。
    """
    messageObj =Message(sayer="user", text=message,timestamp=datetime.now())
    response_text = await ai_service.chat(message)
    create_or_get_chat_history(user_id, repo_id)
    
    response=Message(sayer="assistant", text=response_text,timestamp=datetime.now())

    update_chat_history(user_id, repo_id, messageObj, response)
    return response


@router.post("/{user_id}/{repo_id}/with-file", response_model=Message)
async def chat_with_file(user_id: str, repo_id: str, message: str, file: UploadFile = File(...)):
    """
    处理包含文件上传的聊天请求。

    参数:
        user_id (str): 用户的ID。
        repo_id (str): 仓库的ID。
        message (str): 用户发送的消息。
        file (UploadFile): 用户上传的文件。

    返回:
        Message: 助手的响应消息。

    功能:
        1. 获取聊天记录。
        2. 处理上传的文件并将其保存到指定目录。
        3. 调用数据结构化和风险预测的主要处理逻辑。
        4. 根据文件内容和风险预测结果生成系统提示。
        5. 调用AI服务生成回复并更新聊天记录。
    """
    create_or_get_chat_history(user_id, repo_id)
    question = message
    store_message = Message(sayer="user", text=message,timestamp=datetime.now())
    # 结构化 - 取出excel - 风险预测 - 风险预测结果加入message
    
    current_file_path = os.path.abspath(__file__)
    # 获得当前文件的父目录
    parent_dir = os.path.dirname(current_file_path)
    parent_dir = os.path.dirname(parent_dir)
    upload_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "SourceData")
    target_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "TargetData")
    json_folder = os.path.join(parent_dir, "services", "DataStructuring", "DataStructuring", "JsonData")
    predict_folder = os.path.join(parent_dir, "services", "risk_prediction", "SourceData")

    # 如果文件夹不存在就新建文件夹
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)
    if not os.path.exists(predict_folder):
        os.makedirs(predict_folder)
    print("\n\n\n")
    print(upload_folder)
    print("\n\n\n")
    '''
        # 获得当前文件路径
        current_file_path = os.path.abspath(__file__)
        # 获得当前文件的父目录
        parent_dir = os.path.dirname(current_file_path)
        parent_dir = os.path.dirname(parent_dir)
        upload_folder = os.path.join("..", parent_dir, "services", "DataStructuring", "DataStructuring", "SourceData")
        json_folder = os.path.join("..", parent_dir, "services", "DataStructuring", "DataStructuring", "JsonData")
    '''
    file_path = os.path.join(upload_folder, file.filename)
    # print("\n***file_path: ", file_path)
    
    # 删除file_path 下的所有文件
    if os.path.exists(upload_folder):
        for _file_name in os.listdir(upload_folder):
            os.remove(os.path.join(upload_folder, _file_name))

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 这里需要添加文件处理逻辑
    main_process.main_process()

    # 将targetData文件夹下的excel文件移动到特定文件夹中，从而风险预测
    # 将predict_folder文件夹清空
   
    if os.path.exists(predict_folder):
        for _file_name in os.listdir(predict_folder):
            os.remove(os.path.join(predict_folder, _file_name))
    
    for _file_name in os.listdir(target_folder):
        shutil.copy(os.path.join(target_folder, _file_name), os.path.join(predict_folder, _file_name))

    predict_results = predict_all()
    print("\n\n\n")
    print(predict_results)
    print("\n\n\n")


    
    # 清空json文件夹
    if os.path.exists(json_folder):
        for _file_name in os.listdir(json_folder):
            os.remove(os.path.join(json_folder, _file_name))
    target_to_json.process_target_to_json()
    
   
    # 获取json_folder文件夹里所有文件的内容
    json_files = glob.glob(os.path.join(json_folder, "*.json"))
    all_files_content = ""
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            all_files_content += f.read() + "\n"

    # 获取文件名
    excel_name = file.filename.split(".")[0] + ".xlsx"
    if predict_results[f'{excel_name}'] == None:
        # 文件信息不全，让大模型给出一定的风险建议
        message = SYSTEM_PROMPT +  message + "\n文件内容如下： " + all_files_content + "\n由于用户上传的文件信息不全，请根据用户上传的文件信息给出一定的风险建议"
    else:
        # 文件信息全，给出风险概率，并让大模型根据风险概率给出建议
        message = SYSTEM_PROMPT + message + "\n文件内容如下： " + all_files_content + "\n用户上传的文件诈骗概率为： " + str(predict_results[f'{excel_name}'])
    response_text = await ai_service.chat(message)
    response=Message(sayer="assistant", text=response_text,timestamp=datetime.now())
    update_chat_history(user_id, repo_id, store_message, response)
    return response



@router.post("/{user_id}/{repo_id}/file", response_model=Message)
async def chat_with_file_id(user_id: str, repo_id: str, file_id: str, message: str):
    """
    处理单个文件的聊天请求，支持不同位置的文件ID。
    """
    # 获取仓库信息
    repo_info = get_repo_by_id(repo_id)
    
     # 在files中查找文件
        
   # 在files中查找文件
        
    files_match = [f for f in repo_info.get('files', []) if convert_objectid( f['file_id']) ==(file_id)]
        
    # 在results中查找文件
    results_match = [r for r in repo_info.get('results', []) if convert_objectid(r['file_id']) == (file_id)]
    # 确定要使用的文件ID
    if files_match:
        # 如果在files中找到，保持原file_id不变
        actual_file_id = file_id
        file_metadata = files_match[0]
    elif results_match:
        # 如果在results中找到，使用source_file
        actual_file_id = results_match[0]['source_file']
        file_metadata = results_match[0]
    else:
        # 如果文件未找到
        return None

    create_or_get_chat_history(user_id, repo_id)
    
    # 使用actual_file_id获取JSON内容
    json_res = get_json_res(actual_file_id)
    
    store_message = Message(sayer="user", text=message, timestamp=datetime.now())
    
    if json_res is None:
        return None
    
    # 获取诈骗概率，优先使用具体的概率值
    fraud_probability = (
        file_metadata.get('status') if 
        file_metadata.get('status') not in ['uploaded', None] 
        else '未知'
    )
    
    message = (
        SYSTEM_PROMPT + 
        message + 
        "\n文件内容如下： " + 
        str(json_res["content"]) + 
        "\n用户上传的文件诈骗概率为： " + 
        str(fraud_probability)
    )
    
    print(message)
    response_text = await ai_service.chat(message)
    response = Message(sayer="assistant", text=response_text, timestamp=datetime.now())
    
    update_chat_history(user_id, repo_id, store_message, response)
    return response

@router.post("/{user_id}/{repo_id}/multiple_files", response_model=Message)
async def chat_with_multiple_files(
    user_id: str, 
    repo_id: str, 
    file_ids: List[str],
    message: str
):
    """
    处理多文件聊天请求，支持不同位置的文件ID。
    """
    # 获取仓库信息
    repo_info = get_repo_by_id(repo_id)
    print(repo_info)
    print(type(repo_info))
    create_or_get_chat_history(user_id, repo_id)
    
    store_message = Message(sayer="user", text=message, timestamp=datetime.now())
    
    file_contents = []
    
    for file_id in file_ids:
        # 在files中查找文件
        
        files_match = [f for f in repo_info.get('files', []) if convert_objectid( f['file_id']) ==(file_id)]
        
        # 在results中查找文件
        results_match = [r for r in repo_info.get('results', []) if convert_objectid(r['file_id']) == (file_id)]
        
        # 确定要使用的文件ID
        if files_match:
            # 如果在files中找到，保持原file_id不变
            actual_file_id = file_id
            file_metadata = files_match[0]
        elif results_match:
            # 如果在results中找到，使用source_file
            actual_file_id = results_match[0]['source_file']
            file_metadata = results_match[0]
        else:
            # 如果文件未找到，跳过
            print("reach here")

            continue
        
        # 获取JSON内容
        json_res = get_json_res(actual_file_id)
        
        if json_res is None:
            continue
        
        # 获取诈骗概率，优先使用具体的概率值
        fraud_probability = (
            file_metadata.get('status') if 
            file_metadata.get('status') not in ['uploaded', None] 
            else '未知'
        )
        
        file_contents.append({
            "file_id": file_id,
            "content": str(json_res["content"]),
            "fraud_probability": str(fraud_probability),
            "file_name": file_metadata.get('filename', '未知文件')
        })
    
    # 如果没有有效文件，返回None
    if not file_contents:
        return None
    
    # 构建消息
    message_parts = [SYSTEM_PROMPT, message]
    
    # 添加多个文件的内容和诈骗概率
    for file_info in file_contents:
        message_parts.append(f"\n文件 {file_info['file_name']} 的内容如下：{file_info['content']}")
        message_parts.append(f"文件 {file_info['file_name']} 的诈骗概率为：{file_info['fraud_probability']}")
    
    # 合并消息
    full_message = "\n".join(message_parts)
    
    # 调用AI服务
    print(full_message)
    response_text = await ai_service.chat(full_message)
    
    # 创建响应消息
    response = Message(sayer="assistant", text=response_text, timestamp=datetime.now())
    
    # 更新聊天历史
    update_chat_history(user_id, repo_id, store_message, response)
    
    return response
