# coding= gbk
from .MyFunctions import *
import pandas as pd

# 修改后的代码
import os
import requests

# 定义 Ollama API 地址
OLLAMA_API_URL = "http://localhost:11434/api/generate"
def txt_to_excel(folder_path,output_path):
    # 使用原始字符串定义要检索的文件夹路径
    all=['交易ID', '交易类型', '交易金额', '交易币种', '交易频率', '小额交易', '设备信息', 
        '交易时间', '操作时长', '初始账户旧余额', '初始账户新余额', '初始账户开户信息', 
        '初始账户信用等级', '初始账户地址', '初始账户年龄', '初始账户职业', '初始账户教育水平', 
        '初始账户联系方式', '目标账户名', '目标账户旧余额', '目标账户新余额', '目标账户开户信息',
        '目标账户信用等级', '目标账户地址', '目标账户年龄', 
        '目标账户职业', '目标账户教育水平', '目标账户联系方式', '是否欺诈', '是否标记为欺诈']
    # 定义指定的 prompt
    # prompt_template = "请分析以下文本内容：{}"

    def read_txt_files(folder):
        """
        递归检索指定文件夹中的所有 txt 文件并读取内容
        """
        txt_contents = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # print(content)
                            print('处理',file)
                            print('----------------------------------------------')
                            # 获取表头出版汇总 的 绝对路径
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            target_file=os.path.join(current_dir,'./表头初版汇总.xlsx')
                            target=pd.read_excel(target_file)
                            print(target)
                            for context in all:
                                print('处理',context,'指标')
                                print('----------------------------------------------')
                                prompt=get_prompt(context)
                                response=''
                                try:
                                    response = get_ollama_response(prompt+content)
                                    print(response)
                                    if context=='设备信息' or context=='初始账户开户信息' or context=='目标账户开户信息':
                                        pass
                                    elif context=='是否欺诈'or context=='是否标记为欺诈':
                                        if '是欺诈' in response and '不是欺诈' not in response:
                                            response='是'
                                        elif '否' in response or '不是欺诈' in response:
                                            response='否'
                                        else:
                                            response='否'
                                    else:
                                        # response=extract(context,response)
                                        pattern = r'[：:](.*?)(?:\n|$|。)'
                                        matches = re.findall(pattern, response, re.DOTALL)
                                        results = [match.strip() for match in matches if match.strip()]
                                        pattern_dash = r'-(.*?)(?:\n|$|。)'
                                        matches_dash = re.findall(pattern_dash, response, re.DOTALL)
                                        results_dash = [match.strip() for match in matches_dash if match.strip()]
                                        pattern_quote = r'“(.*?)”'
                                        matches_quote = re.findall(pattern_quote, response)
                                        results_quote =[match.strip() for match in matches_quote if match.strip()]
                                        pattern_s = r'```(.*?)```'
                                        matches_s = re.findall(pattern_s, response, re.DOTALL)
                                        results_s=[match.strip() for match in matches_s if match.strip()]
                                        # 提取两个 | 之间的内容
                                        pattern_pipe = r'\|(.*?)(?:\n|$|。)'
                                        matches_pipe = re.findall(pattern_pipe, response, re.DOTALL)
                                        results_pipe = [match.strip() for match in matches_pipe if match.strip()]
                                        lines = response.splitlines()
                                        r = []
                                        i = 0
                                        while i < len(lines):
                                            if lines[i].strip() == '':  # 找到一个空行
                                                start_index = i + 1
                                                # 找到下一个空行
                                                j = start_index
                                                while j < len(lines) and lines[j].strip() != '':
                                                    j += 1
                                                end_index = j
                                                # 如果两个空行之间只有一行内容
                                                if end_index - start_index == 1 and start_index!=len(lines)-1 and start_index!=0 and len(lines[start_index])<30:
                                                    r.append(lines[start_index].strip())
                                                i = end_index
                                            else:
                                                i += 1
                                        if results_s:
                                            response=results_s[0]
                                        elif results_dash:
                                            response=results_dash[0]
                                        elif r:
                                            response=r[-1]
                                        elif results:
                                            response=results[0]
                                        elif results_quote:
                                            response=results_quote[-1]
                                        elif results_pipe:
                                            response=results_pipe[0]
                                        else:
                                            response='无'
                                    print('response',response)
                                except:
                                    response='无'
                                    print('获取信息失败')
                                condition=target['表头中具体条目']==context
                                target.loc[condition,'内容']=response
                                print('----------------------------------------------')
                            #     print("成功填写")
                            # response=get_ollama_response(f"请基于{content}回答以下列表中每一项的信息{all}")
                            # print(response)

                            target_file=output_path+'\\'+file[:-3]+'xlsx'
                            print("----------------------------------------------\n")
                            print(f"\n*** for debug: target_file: {target_file}")
                            target.to_excel(target_file,index=False)
                            print("----------------------------------------------\n")
                            txt_contents.append(content)
                    except Exception as e:
                        print(f"读取文件 {file_path} 时出错: {e}")
        print(txt_contents)                
        return txt_contents

    def get_ollama_response(prompt):
        """
        向 Ollama API 发送请求并获取响应
        """
        data = {
            "model": "wangshenzhi/llama3-8b-chinese-chat-ollama-q4",
            "prompt": prompt,
            "stream": False,
            "temperature":0,
            "num_predict": 1,
            "top_k": 1,
            "top_p": 1.0
        }
        try:
            response = requests.post(OLLAMA_API_URL, json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.RequestException as e:
            print(f"请求 Ollama API 时出错: {e}")
            return None

    txt_contents = read_txt_files(folder_path)
    print("成功处理以下文件：",txt_contents)