# 非结构化转结构化文档
## 在浏览项目之前，请先阅读本文档
### 代码已经考虑了一些异常情况，若在实际运行过程中还有其他报错，随时反馈

# 有关于输入
目前仅支持对以下非结构化类型数据进行处理（注意不支持扫描版pdf）
```
"pdf","docx","doc","xls","xlsx","ppt","pptx",
"png","jpg","jpeg","csv","py","txt","md","bmp","gif",
"mp3","m4a","wav"
```
请将“所有”的输入数据文件都放置到 [SourceData](SourceData) 这个文件目录下面，随后开始自动处理

注意： [SourceData](SourceData) 内部应当全部都是文件，不包含任何文件夹

对语音转文字部分花费时间比较多，个人建议少弄点音频类数据

如果提取过一次txt数据的话，就不用每一次从头再来，可以将如下部分注释掉只使用提取过后的txt数据去做接下来的工作
```python
    # 将部分文件夹清空
    Clear_Dir([TextPath,Input_for_ShenZijun_Path,TargetPath])
    # Clear_Dir([Input_for_ShenZijun_Path, TargetPath])
    # 将SourcePath文件提取文字并放入TextPath当中
    ProcessData(SourcePath,TextPath)
```

txt_to_excel是将txt转为excel的过程，最终会放在Target_folder下










# 常见问题
## 运行时出现如下Warning，不影响整体运行但是看着很烦
```
RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work
  warn("Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work", RuntimeWarning)
```
此时因为系统缺少相应的库导致的，所以需要注意你的电脑需要安装ffmpeg

对于Ubuntu系统请运行
```shell
sudo apt install ffmpeg
```
如果遇到相关报错，请检查相关更新或STFW寻求解决方案
```shell
sudo apt clean
sudo apt update
```

对于Windows系统，如果你有git bash的话，请在git bash的shell中运行以下命令
```bash
pacman -S ffmpeg
```
如果没有git bash的话，请在windows的命令行窗口当中运行以下完整的命令行脚本
```bash
# 以管理员身份运行 PowerShell 或命令提示符

# 设置执行策略
Set-ExecutionPolicy Bypass -Scope Process -Force

# 更新安全协议
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

# 安装 Chocolatey
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# 安装 FFmpeg
choco install ffmpeg -y

# 验证安装
ffmpeg -version
```

## 文件说明
[SourceData](SourceData)文件夹存储的是源数据，就是各种非结构化数据，但是根据每个用户的不同需要创建各自的子文件夹，另外不同的文件尽量文件名不要一样，
即使后缀不一样，因为转换成txt之后的文件名就不太好取了。如果一样的话比如一个 a.doc 一个a.pdf， 转换之后的文件都变成了 a.txt

[TargetData](TargetData)文件夹存储的是转换之后的数据，都是文本类型的数据，然后路径结构啥的跟SourceData几乎一模一样

[main.py](main.py) 这个就不用多说了

[DataProcess.py](DataProcess.py) 用来作为一个抽象层实现文件读写和分发事件处理的逻辑，主要调用GeneralProcess.py和ParticularProcess.py文件

[GeneralProcess.py](GeneralProcess.py) 主要实现对 
.PDF .DOCX .DOC .XLS .XLSX .PPT .PPTX .PNG .JPG .JPEG .CSV .PY .TXT .MD .BMP .GIF
类型的数据进行转换，并且只限制于这些类型的数据

[ParticularProcess.py](ParticularProcess.py)用于对特定类型的数据进行转换，但是目前暂时只支持音频类型的数据，对于视频类型的数据以后再说

[XunFei_to_text.py](XunFei_to_text.py)这个文件是科大讯飞官网给出的api调用的demo代码模板，但是我寻思着这封装的也太差了，还需要我另开一个.py文件
其他的接口都是直接调用一个函数就行，这个倒好还要我copy一份代码，大无语……

[MyFunctions.py](MyFunctions.py)这个文件就有点类似于utils的工具包，里面都是一些个人要用的小函数，比如创建文件，检查路径之类的

[test_for_google.py](test_for_google.py)这个文件是我一开始为了测试google音频转文字而写的一个代码，跟主体架构没有半毛钱关系，不用管

[environment.yml](environment.yml)这个文件我是用```conda env export > environment.yml```命令导出的环境，可以自行搜索相应的命令将这个环境安装到自己这里
我本来想着直接把我这里的conda虚拟环境对应的文件夹压缩成一个压缩包然后发过去，但是后来一想我的电脑是用ubuntu系统的，可能与其他的不兼容，遂采用.yml的方法了

[requirements.txt](requirements.txt)这个文件也就不用我多说了



## 请关闭你的VPN代理（梯子）
如果在shell当中运行的话，请确保你的代理VPN是关掉的，因为我自己试过，我用Ubuntu系统运行的时候（由于平时一直默认都是要开着VPN的）
在shell里面运行main.py的话会报错，会显示以下的报错信息，因为zhipuai是没有办法在开着代理的情况下运行的。