from MyFunctions import *
## 导入处理音频类型数据所需要的库
from pydub import AudioSegment
import speech_recognition as sr
import yaml


def AudioFile(filepath, type):
    """主要是音频文件处理转换成语音文字"""
    # 在我们能够处理 M4A 文件之前，需要将其转换为 WAV 格式
    if type != "wav":
        WavPath = pattern_substitute(filepath, suffix=".wav")
        create_file(WavPath)
        Convert_to_WAV(filepath, type, WavPath)
        filepath = WavPath
    ### 有了 WAV 文件后，我们就可以使用 SpeechRecognition 库进行语音识别了。
    context=recognize_speech_from_wav(wav_file=filepath)
    # 将内容进行返回
    return context


def recognize_speech_from_wav(wav_file):
    # 创建识别器实例
    recognizer = sr.Recognizer()
    # 读取 WAV 文件
    with sr.AudioFile(wav_file) as source:
        # 记录音频数据
        audio_data = recognizer.record(source)
    #print("读取WAV文件结束")
    # 调用 google 的语音识别 API 进行识别
    try:
        # text = recognizer.recognize_google(audio_data, language='zh-CN')
        text = recognizer.recognize_google(audio_data, language='zh-CN')
        #print("调用Google的语音识别API结束")
        return text
    except sr.UnknownValueError:
        #print("未能理解音频")
        return "未能理解音频"
    except sr.RequestError as e:
        #print("请求错误")
        return f"请求错误：{e}"


if __name__=="__main__":
    # 保存原始的 socket 类
    original_socket = socket.socket
    # proxy_path="VPN_proxy.yaml"
    # proxy_config=read_proxy_config(proxy_path)
    # # #print(proxy_config)
    # set_proxy_env(proxy_config)
    path=f"SourceData/语音.mp3"
    content=AudioFile(path,"mp3")
    #print(content)
    # restore_default_proxy()
    restore_default_network(original_socket)

