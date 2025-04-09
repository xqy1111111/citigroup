######## 对于一般性的数据主要采用 zhipuai 的大模型接口进行数据处理 ##############
from pathlib import Path
from zhipuai import ZhipuAI
import json

client = ZhipuAI(
    api_key="5efee394f9ce40898b8b4971c2404f0f.HFvBPToOiej8YoI7",
    #base_url="https://open.bigmodel.cn/api/paas/v4"
)


# 用于上传文件
# 格式限制：.PDF .DOCX .DOC .XLS .XLSX .PPT .PPTX .PNG .JPG .JPEG .CSV .PY .TXT .MD .BMP .GIF
# 文件大小不超过50M，图片大小不超过5M、总数限制为100个文件
# 注意由于文件格式的限制  因此在这里需要先进行判断
def GeneralFile(filepath):
    """
    GeneralFile函数用于处理一般性文件数据  严格要求为以下格式文件：
    .PDF .DOCX .DOC .XLS .XLSX .PPT .PPTX .PNG .JPG .JPEG .CSV .PY .TXT .MD .BMP .GIF
    返回值为文件内容的字符串
    """
    delete_uploaded_files()
    # filepath=f"./pictures/pic1.png"
    file_object = client.files.create(file=Path(filepath), purpose="file-extract")
    # 文件内容抽取
    file_content = client.files.content(file_id=file_object.id).content.decode()
    # #print(file_content)
    # 删除云端文件(由于累计最大限制100个文件，需要及时从云端删除相应的文件)
    delete_single_file(file_object)
    # 使用json.loads()函数将字符串解析为字典
    data_dict = json.loads(file_content)
    #将文件内容作为字符串进行返回
    content = data_dict['content']
    return content















def delete_uploaded_files():
    """删除已经上传的所有文件"""
    # 获取当前以已上传文件的数量
    files = client.files.list(purpose="file-extract")
    # #print(files)
    # 遍历文件列表，删除每个文件
    for file in files.data:
        file_id = file.id
        try:
            # 删除文件
            client.files.delete(file_id=file_id)
            #print(f"Deleted file with ID: {file_id}")
        except Exception as e:
            print(f"Failed to delete file with ID: {file_id}. Error: {e}")


def delete_single_file(file_object):
    """删除上传的单个文件"""
    file_id = file_object.id
    try:
        # 删除文件
        client.files.delete(file_id=file_object.id)
        #print(f"Deleted file with ID: {file_id}")
    except Exception as e:
        print(f"Failed to delete file with ID: {file_id}. Error: {e}")
    return
