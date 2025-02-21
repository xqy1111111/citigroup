# coding= gbk
from .MyFunctions import *
import pandas as pd

# �޸ĺ�Ĵ���
import os
import requests

# ���� Ollama API ��ַ
OLLAMA_API_URL = "http://localhost:11434/api/generate"
def txt_to_excel(folder_path,output_path):
    # ʹ��ԭʼ�ַ�������Ҫ�������ļ���·��
    all=['����ID', '��������', '���׽��', '���ױ���', '����Ƶ��', 'С���', '�豸��Ϣ', 
        '����ʱ��', '����ʱ��', '��ʼ�˻������', '��ʼ�˻������', '��ʼ�˻�������Ϣ', 
        '��ʼ�˻����õȼ�', '��ʼ�˻���ַ', '��ʼ�˻�����', '��ʼ�˻�ְҵ', '��ʼ�˻�����ˮƽ', 
        '��ʼ�˻���ϵ��ʽ', 'Ŀ���˻���', 'Ŀ���˻������', 'Ŀ���˻������', 'Ŀ���˻�������Ϣ',
        'Ŀ���˻����õȼ�', 'Ŀ���˻���ַ', 'Ŀ���˻�����', 
        'Ŀ���˻�ְҵ', 'Ŀ���˻�����ˮƽ', 'Ŀ���˻���ϵ��ʽ', '�Ƿ���թ', '�Ƿ���Ϊ��թ']
    # ����ָ���� prompt
    # prompt_template = "����������ı����ݣ�{}"

    def read_txt_files(folder):
        """
        �ݹ����ָ���ļ����е����� txt �ļ�����ȡ����
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
                            print('����',file)
                            print('----------------------------------------------')
                            # ��ȡ��ͷ������� �� ����·��
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            target_file=os.path.join(current_dir,'./��ͷ�������.xlsx')
                            target=pd.read_excel(target_file)
                            print(target)
                            for context in all:
                                print('����',context,'ָ��')
                                print('----------------------------------------------')
                                prompt=get_prompt(context)
                                response=''
                                try:
                                    response = get_ollama_response(prompt+content)
                                    print(response)
                                    if context=='�豸��Ϣ' or context=='��ʼ�˻�������Ϣ' or context=='Ŀ���˻�������Ϣ':
                                        pass
                                    elif context=='�Ƿ���թ'or context=='�Ƿ���Ϊ��թ':
                                        if '����թ' in response and '������թ' not in response:
                                            response='��'
                                        elif '��' in response or '������թ' in response:
                                            response='��'
                                        else:
                                            response='��'
                                    else:
                                        # response=extract(context,response)
                                        pattern = r'[��:](.*?)(?:\n|$|��)'
                                        matches = re.findall(pattern, response, re.DOTALL)
                                        results = [match.strip() for match in matches if match.strip()]
                                        pattern_dash = r'-(.*?)(?:\n|$|��)'
                                        matches_dash = re.findall(pattern_dash, response, re.DOTALL)
                                        results_dash = [match.strip() for match in matches_dash if match.strip()]
                                        pattern_quote = r'��(.*?)��'
                                        matches_quote = re.findall(pattern_quote, response)
                                        results_quote =[match.strip() for match in matches_quote if match.strip()]
                                        pattern_s = r'```(.*?)```'
                                        matches_s = re.findall(pattern_s, response, re.DOTALL)
                                        results_s=[match.strip() for match in matches_s if match.strip()]
                                        # ��ȡ���� | ֮�������
                                        pattern_pipe = r'\|(.*?)(?:\n|$|��)'
                                        matches_pipe = re.findall(pattern_pipe, response, re.DOTALL)
                                        results_pipe = [match.strip() for match in matches_pipe if match.strip()]
                                        lines = response.splitlines()
                                        r = []
                                        i = 0
                                        while i < len(lines):
                                            if lines[i].strip() == '':  # �ҵ�һ������
                                                start_index = i + 1
                                                # �ҵ���һ������
                                                j = start_index
                                                while j < len(lines) and lines[j].strip() != '':
                                                    j += 1
                                                end_index = j
                                                # �����������֮��ֻ��һ������
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
                                            response='��'
                                    print('response',response)
                                except:
                                    response='��'
                                    print('��ȡ��Ϣʧ��')
                                condition=target['��ͷ�о�����Ŀ']==context
                                target.loc[condition,'����']=response
                                print('----------------------------------------------')
                            #     print("�ɹ���д")
                            # response=get_ollama_response(f"�����{content}�ش������б���ÿһ�����Ϣ{all}")
                            # print(response)

                            target_file=output_path+'\\'+file[:-3]+'xlsx'
                            print("----------------------------------------------\n")
                            print(f"\n*** for debug: target_file: {target_file}")
                            target.to_excel(target_file,index=False)
                            print("----------------------------------------------\n")
                            txt_contents.append(content)
                    except Exception as e:
                        print(f"��ȡ�ļ� {file_path} ʱ����: {e}")
        print(txt_contents)                
        return txt_contents

    def get_ollama_response(prompt):
        """
        �� Ollama API �������󲢻�ȡ��Ӧ
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
            print(f"���� Ollama API ʱ����: {e}")
            return None

    txt_contents = read_txt_files(folder_path)
    print("�ɹ����������ļ���",txt_contents)