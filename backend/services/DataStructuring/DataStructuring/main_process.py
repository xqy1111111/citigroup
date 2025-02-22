from .DataProcess import *
from .Clssifier import *
from .txt_to_excel import *


# 注意：在运行之前，请保证SourceData文件夹下其余文件已经被清空，需要处理的文件才在里面

# if __name__=="__main__":
async def main_process():
    # 使用相对路径：
    # 获取当前文件的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))

    SourcePath="./SourceData"
    SourcePath=os.path.join(current_dir,SourcePath)
    TextPath="./TextData"
    TextPath=os.path.join(current_dir,TextPath)
    Input_for_ShenZijun_Path="./InputData_for_ShenZijun"
    Input_for_ShenZijun_Path=os.path.join(current_dir,Input_for_ShenZijun_Path)
    TargetPath="./TargetData"
    TargetPath=os.path.join(current_dir,TargetPath)

    # 将部分文件夹清空
    Clear_Dir([TextPath,Input_for_ShenZijun_Path,TargetPath])
    # Clear_Dir([Input_for_ShenZijun_Path, TargetPath])

    # 将SourcePath文件提取文字并放入TextPath当中
    ProcessData(SourcePath,TextPath)

    print(TextPath)
    print("--------------------------------应该已经完成了传进txt--------------------------------")

    # 对每个txt文件进行问询其结构化程度如何
    Classify(TextPath,Input_for_ShenZijun_Path)

    #结构化所有数据
    txt_to_excel(Input_for_ShenZijun_Path,TargetPath)


