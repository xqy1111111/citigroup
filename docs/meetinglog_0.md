
# Table of Contents

1.  [git 规范](#orgd1633e2)
2.  [前端组件(命名驼峰)(一个人)](#orgd9fab89)
    1.  [sidebar](#org8fd9131)
        1.  [entry](#org78d9cb6)
    2.  [input box](#orgfbe7c7e)
    3.  [navigate bar](#orgfe136d4)
        1.  [button](#orgb693588)
    4.  [chart](#orgb88e852)
        1.  [general](#org185ca52)
        2.  [tree](#org310d23a)
    5.  [profile](#orgf04615d)
    6.  [chat](#org596b42c)
        1.  [input](#org72db344)
        2.  [botton](#orgc87173c)
        3.  [logo](#org4816405)
3.  [page(两个人)](#orgd684127)
    1.  [*home*](#org4c8fede)
    2.  [*repo*](#org6a1a755)
        1.  [repo/id/general](#org309b61c)
        2.  [repo/id/files](#org4fd5f59)
    3.  [chat/](#org4099265)
4.  [后端api(一个人数据库,api + 一个人实现api + 一个人chat+代码融合)](#orgb4a7c00)
    1.  [维护repo与其对应用户的关系](#orgbcf6600)
        1.  [获取repo id](#orgaf68a4c)
        2.  [生成repo id](#orgb50179a)
    2.  [文件存储解析(到对应repo)](#org960dc53)
        1.  [增删查改](#org6d4bc85)
    3.  [repo](#orgc590a08)
        1.  [增加/删除](#orge8652e5)
        2.  [获取](#org37c6064)
    4.  [chat](#org6a65972)
        1.  [存储text(question + answer)](#orgfc7faf3)
        2.  [query ai](#org78a5327)
        3.  [返回回答给前端](#org63e2c78)
    5.  [导出](#org7f67a54)
    6.  [代码的融合](#org0fdce21)
5.  [分配](#org5bd32f0)
    1.  [前端](#orga4e074b)
    2.  [后端](#org7a88a23)



<a id="orgd1633e2"></a>

# git 规范

请不要在main/master分支直接修改，在自己的branch完善后再merge进来

push之前请先拉取解决冲突，不要污染main/master分支


<a id="orgd9fab89"></a>

# 前端组件(命名驼峰)(一个人)


<a id="org8fd9131"></a>

## sidebar


<a id="org78d9cb6"></a>

### entry

history, files, general, input


<a id="orgfbe7c7e"></a>

## input box


<a id="orgfe136d4"></a>

## navigate bar


<a id="orgb693588"></a>

### button


<a id="orgb88e852"></a>

## chart


<a id="org185ca52"></a>

### general


<a id="org310d23a"></a>

### tree


<a id="orgf04615d"></a>

## profile


<a id="org596b42c"></a>

## chat


<a id="org72db344"></a>

### input


<a id="orgc87173c"></a>

### botton


<a id="org4816405"></a>

### logo


<a id="orgd684127"></a>

# page(两个人)


<a id="org4c8fede"></a>

## *home*

选择repo/建立repo

login button


<a id="org6a1a755"></a>

## *repo*

把东西拖进来，看detail等


<a id="org309b61c"></a>

### repo/id/general


<a id="org4fd5f59"></a>

### repo/id/files


<a id="org4099265"></a>

## chat/


<a id="orgb4a7c00"></a>

# 后端api(一个人数据库,api + 一个人实现api + 一个人chat+代码融合)


<a id="orgbcf6600"></a>

## 维护repo与其对应用户的关系


<a id="orgaf68a4c"></a>

### 获取repo id


<a id="orgb50179a"></a>

### 生成repo id


<a id="org960dc53"></a>

## 文件存储解析(到对应repo)

需要考虑预览方便


<a id="org6d4bc85"></a>

### 增删查改


<a id="orgc590a08"></a>

## repo


<a id="orge8652e5"></a>

### 增加/删除


<a id="org37c6064"></a>

### 获取

1.  总的信息

2.  某个repo的文件和信息


<a id="org6a65972"></a>

## chat


<a id="orgfc7faf3"></a>

### 存储text(question + answer)


<a id="org78a5327"></a>

### query ai


<a id="org63e2c78"></a>

### 返回回答给前端


<a id="org7f67a54"></a>

## 导出

返回后端的文件


<a id="org0fdce21"></a>

## 代码的融合


<a id="org5bd32f0"></a>

# 分配


<a id="orga4e074b"></a>

## 前端

王+柯+何


<a id="org7a88a23"></a>

## 后端

剩下的

