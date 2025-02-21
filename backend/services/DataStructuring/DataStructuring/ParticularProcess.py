from .MyFunctions import *
## 导入处理音频类型数据所需要的库
from pydub import AudioSegment
import speech_recognition as sr
# import moviepy.editor
from .XunFei_to_text import *
import assemblyai as aai  #试用了一下确实免费   但是适合处理英文  中文太差了

# Switch_Method = "aai"
# Switch_Method = "google"
Switch_Method = "xunfei"


def AudioFile(filepath, type):
    """主要是音频文件处理转换成语音文字"""
    ### 由于后来不用google转写  使用科大讯飞去转写所以直接用就行
    context = None
    if Switch_Method == "aai":
        context = aai_method(filepath)
    elif Switch_Method == "google":
        context = google_method(filepath,type)
    elif Switch_Method == "xunfei":
        context = xunfei_method(filepath)
    else:#如果都没有特意指定的话就用免费但不好用的aai了
        context = aai_method(filepath)
    # 将内容进行返回
    return context


def xunfei_method(filepath):
    api = RequestApi(appid="046cd81b",
                     secret_key="5b7ce2f76552d228461e602728a2ffed",
                     upload_file_path=filepath)
    result = api.get_result()
    ###  注意此处我们默认所有的音频文件的内容都是中文版的（英文版的话后期再优化吧）
    result=Extract_Chinese(result)
    return result

def aai_method(filepath):
    aai.settings.api_key = "f3042ac8de75498a8898b0006520d5cb"
    # transcriber = aai.Transcriber()
    # transcript = transcriber.transcribe(wav_file)
    config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.nano)
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(filepath)
    text=transcript.text
    return text

def google_method(filepath, type):
    # 在我们能够处理 M4A 文件之前，需要将其转换为 WAV 格式
    if type != "wav":
        WavPath = pattern_substitute(filepath, suffix=".wav")
        create_file(WavPath)
        Convert_to_WAV(filepath, type, WavPath)
        filepath = WavPath
    ### 有了 WAV 文件后，我们就可以使用 SpeechRecognition 库进行语音识别了。
    content = google_speech_from_wav(filepath)
    return content

def google_speech_from_wav(wav_file):
    # 创建识别器实例
    recognizer = sr.Recognizer()
    # 读取 WAV 文件
    with sr.AudioFile(wav_file) as source:
        # 记录音频数据
        audio_data = recognizer.record(source)
    print("读取WAV文件结束")
    # 调用  的语音识别 API 进行识别
    try:
        # text = recognizer.recognize_google(audio_data, language='zh-CN')
        text = recognizer.recognize_google(audio_data, language='zh-CN')
        print("调用Google的语音识别API结束")
        return text
    except sr.UnknownValueError:
        print("未能理解音频")
        return "未能理解音频"
    except sr.RequestError as e:
        print("请求错误")
        return f"请求错误：{e}"



# if __name__=="__main__":
#     path=f"SourceData/模拟数据（改）/语音记录.m4a"
#     content=AudioFile(path,"m4a")
#     print(content)


