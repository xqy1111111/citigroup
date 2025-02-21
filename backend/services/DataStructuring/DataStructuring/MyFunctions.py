# MyFunctions.py文件用于一些自己写的小函数  类似于utils工具的作用
import filetype
import os
import re
import json
from pydub import AudioSegment
import shutil
import yaml
import urllib.request
import socks
import socket
from pathlib import Path
import shutil


def FileTypeRecognize(filepath):
    """
    这个函数用于识别各种各样的文件类型   通过调用 filetype 的包进行识别
    """
    type = filetype.guess(filepath)
    if type is None:
        print('无法识别文件类型...')
        return None  #如果没有办法识别的话那就返回None  但是这个时候需要注意调用它就得手动judge一下
    print(f'{filepath}路径对应的文件是个{type.extension}文件，MIME类型是{type.mime}')
    return type.extension

def CheckDirExist(DirPath):
    """这个函数是用来检查是否存在对应的文件夹路径"""
    if not os.path.exists(DirPath):
        print(f"路径不存在: {DirPath}")
        return None
    if not os.path.isdir(DirPath):
        print(f"给定的路径不是一个目录: {DirPath}")
        return None
    return 1


def pattern_substitute(filepath, suffix):
    """这个函数用于将所有的文件后缀转化为.txt"""
    pattern = re.compile(r'(.*)(\.[^.]+)$')
    new_path = re.sub(pattern, rf'\1{suffix}', filepath)
    return new_path


def write_to_txt_os(filepath, content):
    """这个函数是用于将content内容传入给对应的filepath并且只要确保最高级的父目录存在的话，使用 os 模块创建目录，如果中间的目录不存在，它会递归地创建它们"""
    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)  # 确保父目录存在
        with open(filepath, 'w') as file:
            file.write(content)
        print(f"文件 {filepath} 已成功创建并写入内容。")
    except Exception as e:
        print(f"创建或写入文件时出错: {e}")



def create_file(filepath):
    try:
        # 以写入模式打开文件，如果文件不存在会创建文件
        with open(filepath, 'w') as file:
            pass  # 这里不进行写入操作，仅创建文件
        print(f"文件 {filepath} 已成功创建。")
    except Exception as e:
        print(f"创建文件时出错: {e}")



def Extract_Chinese(json_data):
    """这个函数用于将json表达式当中的中文提取出来"""
    # 解析JSON字符串
    str_data=str(json_data)
    # 使用正则表达式匹配所有中文字符
    chinese_parts = re.findall(r'[\u4e00-\u9fff]+', str_data)
    # 将匹配到的中文字符拼接成一个字符串
    chinese_text = ''.join(chinese_parts)
    # 打印结果
    print(chinese_text)
    return chinese_text



def Convert_to_WAV(filepath,type,WavPath):
    """这个函数用于将其他格式的音频文件转化为 WAV 格式"""
    audio=None
    if type=="m4a":
        audio=AudioSegment.from_file(filepath,format="m4a")
    elif type=="mp3":
        audio=AudioSegment.from_mp3(filepath)
    if not audio:
        print("此时的audio是 None 出现问题！！！！")
    audio.export(WavPath,format="wav")
    return


def Clear_Dir(DirList):
    """用于清空指定文件夹下面的内容的"""
    for Dir in DirList:
        try:
            # 删除整个文件夹
            shutil.rmtree(Dir)
            # 重新创建文件夹
            os.makedirs(Dir)
            print(f"Folder '{Dir}' has been cleared and recreated.")
        except Exception as e:
            print(f"Failed to clear folder '{Dir}'. Reason: {e}")



def read_proxy_config(file_path):
    """读取YAML文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            config = yaml.safe_load(file)
            return config
        except yaml.YAMLError as e:
            print(f"Error reading YAML file: {e}")
            return None


def set_proxy_env(config):
    """设置代理环境变量"""
    if config and 'mixed-port' in config:
        proxy_port = config['mixed-port']
        proxy_url = f'http://127.0.0.1:{proxy_port}'
        os.environ['http_proxy'] = proxy_url
        os.environ['https_proxy'] = proxy_url
        print(f"Proxy set to: {proxy_url}")
    else:
        print("Proxy configuration not found.")


def restore_default_proxy():
    """恢复默认代理设置"""
    if 'http_proxy' in os.environ:
        del os.environ['http_proxy']
    if 'https_proxy' in os.environ:
        del os.environ['https_proxy']
    print("Proxy settings restored to default.")




def setup_socks_proxy():
    # 设置 SOCKS 代理
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7897)
    socket.socket = socks.socksocket
def restore_default_network(original_socket):
    # 恢复默认网络配置
    socket.socket = original_socket




def Create_Dirs(Dirs):
    """用于在文件夹下面创建新的文件夹"""
    for Dir in Dirs:
        NewPath=Path(Dir)
        NewPath.mkdir(parents=True, exist_ok=True)
        print(f"Folder '{NewPath}' has been created.")
    return



def copy_file(source_file, destination_folder):
    try:
        # 执行文件复制操作
        shutil.copy2(source_file, destination_folder)
        print(f"文件 {source_file} 已成功复制到 {destination_folder}。")
    except FileNotFoundError:
        print(f"源文件 {source_file} 未找到。")
    except PermissionError:
        print("没有足够的权限进行复制操作。")
    except Exception as e:
        print(f"复制文件时出现错误: {e}")

def get_prompt(context):
    context_all={
    "交易ID": {
        "解释": "每笔交易的唯一标识符。",
        "示例": ["TX202405100001", "TX202406150002", "TX202407200003"]
    },
    "交易类型": {
        "解释": "描述交易的类型，如转账、支付、取款、存款等。此分类变量有助于对不同交易行为进行分类。",
        "示例": ["转账", "支付", "取款", "存款", "缴费"]
    },
    "交易金额": {
        "解释": "交易涉及的金融数额。（可以分为cash in和cash out）",
        "示例": ["100.00", "5000.50", "20000", "0.99", "1500.25"]
    },
    "交易币种": {
        "解释": "交易涉及的货币类型。",
        "示例": ["CNY", "USD", "EUR", "GBP", "JPY"]
    },
    "交易频率": {
        "解释": "交易是单次的还是连续多笔类似交易。",
        "示例": ["单次交易", "连续3笔类似交易", "连续5笔类似交易", "连续2笔类似交易"]
    },
    "小额交易": {
        "解释": "该账户近期是否存在多笔小额交易。",
        "示例": ["是", "否"]
    },
    "设备信息": {
        "解释": "使用哪个设备进行的交易，如IP地址、设备类型等。",
        "示例": ["IP: 192.168.1.100, 设备类型: 手机", "IP: 10.0.0.5, 设备类型: 电脑", "IP: 172.16.1.20, 设备类型: 平板"]
    },
    "交易时间": {
        "解释": "交易发生的具体时间戳，是否为夜间等可能存在异常的时间。",
        "示例": ["2024-01-01 23:59:59", "2024-03-15 12:30:00", "2024-07-05 02:15:30", "2024-10-20 18:45:00"]
    },
    "操作时长": {
        "解释": "例如，正常客户在转账时会仔细核对信息，停留时间较长，而欺诈者为快速完成交易，操作可能较为急促，停留时间短。",
        "示例": ["30秒", "2分钟", "50秒", "1分30秒", "45秒"]
    },
    "初始账户旧余额": {
        "解释": "代表交易发生前初始账户的余额，为理解账户余额变化提供了一个参考点。",
        "示例": ["10000.00", "500.25", "2000.50", "100.99", "50000"]
    },
    "初始账户新余额": {
        "解释": "反映交易处理后初始账户的余额，有助于了解交易对账户余额的影响。",
        "示例": ["5000.00", "200.75", "1500.20", "50.50", "45000"]
    },
    "初始账户开户信息": {
        "解释": "初始账户开户时所提供的各项信息，包括开户时间、开户地点等。",
        "示例": ["开户时间: 2020-05-10，开户地点: 中国工商银行XX分行", "开户时间: 2021-08-18，开户地点: 招商银行XX支行", "开户时间: 2019-12-25，开户地点: 建设银行XX分理处"]
    },
    "初始账户信用等级": {
        "解释": "对初始账户信用状况的评级，用于评估账户的信用风险。",
        "示例": ["A", "B", "C", "AA", "BB"]
    },
    "初始账户地址": {
        "解释": "初始账户所有者登记的居住或经营地址。",
        "示例": ["北京市朝阳区XX路XX号", "上海市浦东新区XX街XX号", "广州市天河区XX巷XX弄", "深圳市福田区XX大厦XX座"]
    },
    "初始账户年龄": {
        "解释": "初始账户从开户到当前的时长。",
        "示例": ["4年", "2年", "6年", "1年", "3年"]
    },
    "初始账户职业": {
        "解释": "初始账户所有者所从事的职业。",
        "示例": ["软件工程师", "教师", "医生", "公务员", "自由职业者"]
    },
    "初始账户教育水平": {
        "解释": "初始账户所有者的受教育程度。",
        "示例": ["本科", "硕士", "博士", "大专", "高中"]
    },
    "初始账户联系方式": {
        "解释": "初始账户所有者登记的联系电话或电子邮箱等。",
        "示例": ["13800138000", "13900139000", "example1@example.com", "example2@example.net"]
    },
    "目标账户名": {
        "解释": "作为每笔交易中接收资金的目标账户或实体的标识符。它有助于追踪资金的去向。",
        "示例": ["张三", "李四", "王五", "赵六", "孙七"]
    },
    "目标账户旧余额": {
        "解释": "表示交易前目标账户的余额，为评估因入账资金导致的账户余额变化提供了一个基线。",
        "示例": ["2000.00", "100.50", "3000.75", "50.20", "1500"]
    },
    "目标账户新余额": {
        "解释": "代表交易完成后目标账户的余额，有助于了解入账资金对账户余额的影响。",
        "示例": ["7000.00", "200.70", "5000.25", "100.90", "3000"]
    },
    "目标账户开户信息": {
        "解释": "目标账户开户时所提供的各项信息，包括开户时间、开户地点等。",
        "示例": ["开户时间: 2022-03-15，开户地点: 中国银行XX支行", "开户时间: 2023-06-22，开户地点: 交通银行XX分行", "开户时间: 2022-11-08，开户地点: 农业银行XX储蓄所"]
    },
    "目标账户信用等级": {
        "解释": "对目标账户信用状况的评级，用于评估账户的信用风险。",
        "示例": ["B", "C", "D", "BB", "CC"]
    },
    "目标账户地址": {
        "解释": "目标账户所有者登记的居住或经营地址。",
        "示例": ["天津市和平区XX道XX号", "重庆市渝中区XX街XX号", "杭州市西湖区XX巷XX弄", "南京市鼓楼区XX大厦XX座"]
    },
    "目标账户年龄": {
        "解释": "目标账户从开户到当前的时长。",
        "示例": ["2年", "1年", "3年", "5年", "4年"]
    },
    "目标账户职业": {
        "解释": "目标账户所有者所从事的职业。",
        "示例": ["教师", "会计", "设计师", "司机", "厨师"]
    },
    "目标账户教育水平": {
        "解释": "目标账户所有者的受教育程度。",
        "示例": ["硕士", "大专", "中专", "本科", "初中"]
    },
    "目标账户联系方式": {
        "解释": "目标账户所有者登记的联系电话或电子邮箱等。",
        "示例": ["13600136000", "13700137000", "target1@example.com", "target2@example.org"]
    },
    "是否欺诈": {
        "解释": "一个二元指标是或否，是表示该交易为欺诈交易，否表示为合法交易。这是欺诈检测建模的目标变量。",
        "示例": ["0", "1"]
    },
    "是否标记为欺诈": {
        "解释": "另一个二元指标是或否，用于表明一笔交易是否被标记为潜在欺诈。这可作为欺诈检测算法的一个额外特征。",
        "示例": ["0", "1"]
    }
}
    content=context_all[context]
    return f"请提取并只输出给定文本中的{context}指标，其中{context}指标含义为{content['解释']}，目标文本内容为"  
def extract(context,response):
    import re

    # 定义一个函数，用于从大模型回答中提取交易 ID
    def extract_transaction_id(response):
        pattern = r'交易ID\s*:\s*([\w-]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取交易类型
    def extract_transaction_type(response):
        pattern = r'交易类型\s*:\s*([\u4e00-\u9fa5a-zA-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取交易金额
    def extract_transaction_amount(response):
        pattern = r'交易金额\s*:\s*([\d.]+)'
        match = re.search(pattern, response)
        if match:
            return float(match.group(1))
        return '无'

    # 定义一个函数，用于从大模型回答中提取交易币种
    def extract_transaction_currency(response):
        pattern = r'交易币种\s*:\s*([A-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取交易频率
    def extract_transaction_frequency(response):
        pattern = r'交易频率\s*:\s*([\u4e00-\u9fa5a-zA-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取小额交易情况
    def extract_small_transaction(response):
        pattern = r'小额交易\s*:\s*(是|否)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取设备信息
    def extract_device_info(response):
        pattern = r'设备信息\s*:\s*(.*)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取交易时间
    def extract_transaction_time(response):
        pattern = r'交易时间\s*:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取操作时长
    def extract_operation_duration(response):
        pattern = r'操作时长\s*:\s*([\d.]+(?:分|秒))'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户旧余额
    def extract_initial_account_old_balance(response):
        pattern = r'初始账户旧余额\s*:\s*([\d.]+)'
        match = re.search(pattern, response)
        if match:
            return float(match.group(1))
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户新余额
    def extract_initial_account_new_balance(response):
        pattern = r'初始账户新余额\s*:\s*([\d.]+)'
        match = re.search(pattern, response)
        if match:
            return float(match.group(1))
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户开户信息
    def extract_initial_account_opening_info(response):
        pattern = r'初始账户开户信息\s*:\s*(.*)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户信用等级
    def extract_initial_account_credit_rating(response):
        pattern = r'初始账户信用等级\s*:\s*([A-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户地址
    def extract_initial_account_address(response):
        pattern = r'初始账户地址\s*:\s*(.*)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户年龄
    def extract_initial_account_age(response):
        pattern = r'初始账户年龄\s*:\s*([\d]+年)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户职业
    def extract_initial_account_occupation(response):
        pattern = r'初始账户职业\s*:\s*([\u4e00-\u9fa5a-zA-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户教育水平
    def extract_initial_account_education_level(response):
        pattern = r'初始账户教育水平\s*:\s*([\u4e00-\u9fa5a-zA-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取初始账户联系方式
    def extract_initial_account_contact_info(response):
        pattern = r'初始账户联系方式\s*:\s*([\d@.a-zA-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户名
    def extract_target_account_name(response):
        pattern = r'目标账户名\s*:\s*([\u4e00-\u9fa5]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户旧余额
    def extract_target_account_old_balance(response):
        pattern = r'目标账户旧余额\s*:\s*([\d.]+)'
        match = re.search(pattern, response)
        if match:
            return float(match.group(1))
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户新余额
    def extract_target_account_new_balance(response):
        pattern = r'目标账户新余额\s*:\s*([\d.]+)'
        match = re.search(pattern, response)
        if match:
            return float(match.group(1))
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户开户信息
    def extract_target_account_opening_info(response):
        pattern = r'目标账户开户信息\s*:\s*(.*)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户信用等级
    def extract_target_account_credit_rating(response):
        pattern = r'目标账户信用等级\s*:\s*([A-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户地址
    def extract_target_account_address(response):
        pattern = r'目标账户地址\s*:\s*(.*)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户年龄
    def extract_target_account_age(response):
        pattern = r'目标账户年龄\s*:\s*([\d]+年)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户职业
    def extract_target_account_occupation(response):
        pattern = r'目标账户职业\s*:\s*([\u4e00-\u9fa5a-zA-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户教育水平
    def extract_target_account_education_level(response):
        pattern = r'目标账户教育水平\s*:\s*([\u4e00-\u9fa5a-zA-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取目标账户联系方式
    def extract_target_account_contact_info(response):
        pattern = r'目标账户联系方式\s*:\s*([\d@.a-zA-Z]+)'
        match = re.search(pattern, response)
        if match:
            return match.group(1)
        return '无'

    # 定义一个函数，用于从大模型回答中提取是否欺诈信息
    def extract_is_fraud(response):
        pattern = r'是否欺诈\s*:\s*(0|1)'
        match = re.search(pattern, response)
        if match:
            return int(match.group(1))
        return '无'

    # 定义一个函数，用于从大模型回答中提取是否标记为欺诈信息
    def extract_is_marked_as_fraud(response):
        pattern = r'是否标记为欺诈\s*:\s*(0|1)'
        match = re.search(pattern, response)
        if match:
            return int(match.group(1))
        return '无'
    
    extraction_functions = {
    '交易ID': extract_transaction_id,
    '交易类型': extract_transaction_type,
    '交易金额': extract_transaction_amount,
    '交易币种': extract_transaction_currency,
    '交易频率': extract_transaction_frequency,
    '小额交易': extract_small_transaction,
    '设备信息': extract_device_info,
    '交易时间': extract_transaction_time,
    '操作时长': extract_operation_duration,
    '初始账户旧余额': extract_initial_account_old_balance,
    '初始账户新余额': extract_initial_account_new_balance,
    '初始账户开户信息': extract_initial_account_opening_info,
    '初始账户信用等级': extract_initial_account_credit_rating,
    '初始账户地址': extract_initial_account_address,
    '初始账户年龄': extract_initial_account_age,
    '初始账户职业': extract_initial_account_occupation,
    '初始账户教育水平': extract_initial_account_education_level,
    '初始账户联系方式': extract_initial_account_contact_info,
    '目标账户名': extract_target_account_name,
    '目标账户旧余额': extract_target_account_old_balance,
    '目标账户新余额': extract_target_account_new_balance,
    '目标账户开户信息': extract_target_account_opening_info,
    '目标账户信用等级': extract_target_account_credit_rating,
    '目标账户地址': extract_target_account_address,
    '目标账户年龄': extract_target_account_age,
    '目标账户职业': extract_target_account_occupation,
    '目标账户教育水平': extract_target_account_education_level,
    '目标账户联系方式': extract_target_account_contact_info,
    '是否欺诈': extract_is_fraud,
    '是否标记为欺诈': extract_is_marked_as_fraud
    }
    return extraction_functions(context)(response)