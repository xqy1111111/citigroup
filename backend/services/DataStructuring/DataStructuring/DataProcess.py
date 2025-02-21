from .GeneralProcess import *
from .ParticularProcess import *
from .MyFunctions import *
import filetype
import os
import re

AllowTypeSet={"PDF","DOCX","DOC","XLS","XLSX","PPT","PPTX","PNG","JPG","JPEG","CSV","PY","TXT","MD","BMP","GIF",
              "pdf","docx","doc","xls","xlsx","ppt","pptx","png","jpg","jpeg","csv","py","txt","md","bmp","gif"}
AudioTypeSet={"MP3","M4A","WAV",
              "mp3","m4a","wav"}
VideoTypeSet={"MP4","AVI","MPEG","MPG","MPE",
              "mp4","avi","mpeg","mpg","mpe"}

def ProcessData(SourcePath,TextPath):
    """
    该函数仅仅会处理SourceData下面的一层的文件，不会递归进行处理，也不会处理文件夹文件，将所有格式文件转换成文本文件
    这个函数是数据处理流程与逻辑的主体
    """
    # 确保给定的路径存在且是一个目录
    if not CheckDirExist(SourcePath) or not CheckDirExist(TextPath):
        return
    #使用pathlib模块访问目录下的所有文件
    path = Path(SourcePath)
    for filepath in path.rglob('*'):#使用了Path.rglob()方法，它可以递归地查找给定模式（在这个例子中是所有文件'*'）的所有文件路径
        print(f"\n*** for debug: filepath: {filepath}")
        if not filepath.is_file():#如果某个路径对应的不是文件的话那就continue好了 检查每个路径是否是文件，并在找到文件时打印出文件路径。
            print(f"路径{filepath}对应的不是文件")
            continue
        print(filepath)
        # 接下来就是对文件进行具体操作，例如打开文件、读取内容、格式转换等
        type=FileTypeRecognize(filepath)
        content = None
        if type in AllowTypeSet:#如果说这个type是在zhipuai的处理格式范围内的话直接交给大模型去做就好了
            content = GeneralFile(filepath=filepath)
        elif type in AudioTypeSet:
            content = AudioFile(filepath=filepath, type=type)
        else:
            print(f"抱歉，该{type}格式文件{filepath}暂时不支持处理")
            continue
        if not content:
            print(f"抱歉，文件{filepath}其内容为空")
            continue
        NewPath = str(filepath).replace(str(SourcePath.split("/")[-1]), str(TextPath.split("/")[-1]))
        print(f"\n*** for debug: NewPath1: {NewPath}")
        NewPath = pattern_substitute(NewPath,suffix=".txt") #该函数位于 MyFunctions.py 内部
        print(f"\n*** for debug: NewPath2: {NewPath}")
        print(f"新的路径为:{NewPath}")
        write_to_txt_os(NewPath, content = content)
    return







