
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

from db.db_util import create_or_get_chat_history,update_chat_history
router = APIRouter()


ai_service = AIService()

@router.get("/",response_model=ChatHistory)
async def get_chat(user_id: str, repo_id: str):
    """
    得到用户的聊天记录
    """
    return create_or_get_chat_history(user_id, repo_id)



@router.post("/{user_id}/{repo_id}", response_model=Message)
async def chat(message: str, user_id: str, repo_id: str):
    """
    处理用户的聊天请求
    """
    response_text = await ai_service.chat(message)
    update_chat_history(user_id, repo_id, message, response_text)
    return Message(sayer="assistant", text=response_text)
''''''
@router.post("/{user_id}/{repo_id}/with-file", response_model=Message)
async def chat_with_file(user_id: str, repo_id: str, message: str, file: UploadFile = File(...)):
    """
    处理带文件的聊天请求
    """
    question = message
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
    system_prompt = """- Role: 金融风险评估专家和高级金融分析师
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
        message = system_prompt +  message + "\n文件内容如下： " + all_files_content + "\n由于用户上传的文件信息不全，请根据用户上传的文件信息给出一定的风险建议"
    else:
        # 文件信息全，给出风险概率，并让大模型根据风险概率给出建议
        message = system_prompt + message + "\n文件内容如下： " + all_files_content + "\n用户上传的文件诈骗概率为： " + str(predict_results[f'{excel_name}'])
    response_text = await ai_service.chat(message)
    update_chat_history(user_id, repo_id, question, response_text)
    return Message(sayer="assistant", text=response_text)

# @router.get("/history/{user_id}", response_model=List[ChatHistory])
# async def get_chat_history_list(user_id: str):
#     """获取用户的聊天历史列表"""
#     pass

# @router.get("/history/{user_id}/{history_id}/messages", response_model=List[Message])
# async def get_chat_messages(user_id: str, history_id: str):
#     """获取特定聊天历史的消息列表"""
#     pass

# @router.delete("/history/{user_id}/{history_id}")
# async def delete_chat_history(user_id: str, history_id: str):
#     """删除特定的聊天历史"""
#     pass 

