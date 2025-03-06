from .GeneralProcess import *
from .MyFunctions import *

StructureLevels=["结构化数据","半结构化数据","非结构化数据"]

def Classify(InputPath,OutputPath):
    """用于将不同的txt文件按照结构化程度进行分类"""
    # 首先先创建三个子文件夹名字
    SD  = f"{OutputPath}/Structured_Data/"
    SSD = f"{OutputPath}/Semi-Structured_Data/"
    USD = f"{OutputPath}/Unstructured_Data/"
    Create_Dirs([SD,SSD,USD])
    # 遍历所有的文件提取文字信息
    path = Path(InputPath)
    for filepath in path.rglob('*'):  # 使用了Path.rglob()方法，它可以递归地查找给定模式（在这个例子中是所有文件'*'）的所有文件路径
        if not filepath.is_file():  # 如果某个路径对应的不是文件的话那就continue好了 检查每个路径是否是文件，并在找到文件时打印出文件路径。
            #print(f"路径{filepath}对应的不是文件")
            continue
        #print(filepath)
        answer="非结构化数据"
        try:
            # 接下来就是对文件进行具体操作，例如打开文件、读取内容、格式转换等
            content = filepath.read_text(encoding='utf-8')
            # #print(f"文件: {filepath} 的内容:")
            # #print(content)
            # 调用zhipuai接口判断 StructureLevels
            answer = QuiryModel(content=content)
        except Exception as e:
            
            print(f"读取文件 {filepath} 时出错: {e}")
        Classify_in_Dir(filepath,answer,SD,SSD,USD)
    return



def QuiryModel(content):
    response = client.chat.completions.create(
        model="glm-4-flash",  # 请填写您要调用的模型名称
        messages=[
            {"role": "user",
             "content": f"现在需要你对以下文件内容：\n\n "
                        f"{content}\n\n "
                        f"深度分析该文件的结构化程度\n"
                        f"分类标准如下:\n"
                        f"{Principle}\n"
                        #f"回答其结构化程度是 较高、一般、较弱\n "
                        # f"注意你的回答只能是 '较高' 或者 '一般' 或者 '较弱'"
                        f"回答这个文件的数据属于 非结构化数据？结构化数据？还是 半结构化数据？\n"
                        f"注意你的回答只能是 结构化数据/半结构化数据/非结构化数据\n"
                        # f"注意你的回答只能是 非结构化数据/结构化数据/半结构化数据\n"
                        # f"另外还需要注意严格区分 半结构化数据/非结构化数据/结构化数据 \n"
                        # f"如果你在结构化与半结构化之间犹豫不定，以80%概率将其归于半结构化数据\n"
                        f"并且不用给出理由  直接回答是 结构化数据？半结构化数据？非结构化数据？ 即可"
             },
        ],
    )
    answer = response.choices[0].message.content
    #print(answer)
    if answer not in StructureLevels:
        answer = "非结构化数据"
    return answer



# Principle="""
# 结构化数据：\n
# 数据特点\n
# 固定格式：数据以表格形式存在，每行和每列都有明确的字段和数据类型。\n
# 预定义模式：数据结构是预定义的，通常存储在关系数据库中。\n
# 易于查询：可以通过 SQL 等查询语言快速查询和分析。\n
# 常见格式：CSV 文件、Excel 文件、数据库表。\n
# 判断标准\n
# 数据是否以表格形式存在，每行和每列都有明确的字段和数据类型。\n
# 是否可以使用 SQL 查询语言进行操作。\n
#
# 半结构化数据：\n
# 数据特点\n
# 部分结构：数据有一定的结构，但不是严格的表格形式，通常包含键值对、分隔符或嵌套结构。\n
# 灵活性：数据格式较为灵活，可以包含嵌套结构或不规则的字段。\n
# 常见格式：JSON、XML、HTML、带注释的 CSV 文件。\n
# 需要解析：需要特定的解析工具来提取和处理数据。\n
# 判断标准\n
# 数据是否包含键值对、分隔符或嵌套结构。
# 是否需要特定的解析工具来提取和处理数据。\n
# 非结构化数据：数据特点
# 自由文本：数据内容通常是自由文本，没有固定的格式。
# 多媒体内容：可能包含图片、音频、视频等多媒体文件。
# 缺乏结构：没有固定的字段或数据类型，数据内容可以非常灵活。
# 需要预处理：在分析之前通常需要进行大量的预处理，例如文本提取、特征提取等。
# 常见格式：纯文本文件、图片、音频、视频。
# 判断标准
# 数据是否为自由文本或多媒体内容，没有固定的格式。
# 是否需要大量的预处理来提取有用信息。\n
# """


Principle="""
结构化数据：数据是否以表格形式存在，每行和每列都有明确的字段和数据类型。\n
半结构化数据：数据是否包含键值对、分隔符或嵌套结构。\n
非结构化数据：数据是否为自由文本或多媒体内容，没有固定的格式。\n
"""


def Classify_in_Dir(filepath,answer,SD,SSD,USD):
    """将对应文件分类到对应的文件夹下面"""
    if answer == "结构化数据":
        copy_file(filepath,SD)
    elif answer == "半结构化数据":
        copy_file(filepath,SSD)
    else:
        copy_file(filepath,USD)
    return
