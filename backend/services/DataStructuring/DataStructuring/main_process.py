from .DataProcess import *
from .Clssifier import *
from .txt_to_excel import *


# 注意：在运行之前，请保证SourceData文件夹下其余文件已经被清空，需要处理的文件才在里面

# if __name__=="__main__":
def main_process(source_dir=None, target_dir=None):
    # 使用相对路径：
    current_dir = os.path.dirname(os.path.abspath(__file__))

    SourcePath = source_dir if source_dir else os.path.join(current_dir, "SourceData")
    TextPath = os.path.join(current_dir, "TextData")
    Input_for_ShenZijun_Path = os.path.join(current_dir, "InputData_for_ShenZijun")
    TargetPath = target_dir if target_dir else os.path.join(current_dir, "TargetData")

    # 如果文件夹不存在就新建文件夹
    os.makedirs(SourcePath, exist_ok=True)
    os.makedirs(TextPath, exist_ok=True)
    os.makedirs(Input_for_ShenZijun_Path, exist_ok=True)
    os.makedirs(TargetPath, exist_ok=True)

    # 清空文件夹
    Clear_Dir([TextPath, Input_for_ShenZijun_Path, TargetPath])

    # 处理数据
    ProcessData(SourcePath, TextPath)
    #print("--------------------------------应该已经完成了传进txt--------------------------------")

    # 结构化数据
    Classify(TextPath, Input_for_ShenZijun_Path)
    txt_to_excel(Input_for_ShenZijun_Path, TargetPath)
