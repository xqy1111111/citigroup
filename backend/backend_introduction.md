## 项目介绍
这是一个前后端分离项目的后端部分，后端数据库主要使用的是mongodb，使用fastapi框架

## 项目结构
```
backend/
├── __init__.py
├── main.py                 # 应用入口点
├── config/                 # 配置相关
│   ├── __init__.py
│   └── settings.py        # 配置设置
├── api/                    # API路由层
│   ├── __init__.py
│   ├── endpoints/         # API端点
│   │   ├── __init__.py
│   │   ├── users.py      # 用户相关路由
│   │   ├── repos.py      # 仓库相关路由
│   │   ├── files.py      # 文件相关路由
│   │   └── chat.py       # 聊天相关路由
│   └── dependencies.py    # 共享依赖项(认证等)
├── core/                  # 核心功能
│   ├── __init__.py
│   ├── security.py       # 安全相关(认证、权限)
│   └── errors.py         # 错误处理
├── models/               # 数据模型
│   ├── __init__.py
│   ├── user.py          # 用户模型
│   ├── repo.py          # 仓库模型
│   ├── file.py          # 文件模型
│   └── chat.py          # 聊天模型
├── services/            # 业务逻辑层
│   ├── __init__.py
│   ├── user_service.py  # 用户相关业务逻辑
│   ├── repo_service.py  # 仓库相关业务逻辑
│   ├── file_service.py  # 文件处理业务逻辑
│   └── chat_service.py  # 聊天相关业务逻辑
├── db/                  # 数据库相关
│   ├── __init__.py
│   ├── database.py     # 数据库连接
│   └── repositories/   # 数据访问层
│       ├── __init__.py
│       ├── user_repository.py
│       ├── repo_repository.py
│       ├── file_repository.py
│       └── chat_repository.py
├── utils/              # 工具函数
│   ├── __init__.py
│   └── helpers.py     # 通用辅助函数
└── DataStructuring/   # 文件处理模块
    └── DataStructuring/
        ├── main.py
        ├── SourceData/
        └── TargetData/
```

## 层次结构说明

### 1. API层 (api/)
- 处理HTTP请求和响应
- 路由定义和基本的请求验证
- 调用相应的service层处理业务逻辑

### 2. 服务层 (services/)
- 实现核心业务逻辑
- 协调不同模块之间的交互
- 处理事务和数据一致性

### 3. 数据访问层 (db/repositories/)
- 封装所有数据库操作
- 提供数据CRUD接口
- 处理数据映射和转换

### 4. 模型层 (models/)
- 定义数据模型和验证规则
- 处理数据序列化和反序列化
- 提供模型间关系定义

### 5. 核心层 (core/)
- 提供认证和授权功能
- 处理全局错误和异常
- 实现核心中间件

### 6. 工具层 (utils/)
- 提供通用辅助函数
- 实现共享工具类
- 处理日志等基础功能

## 主要功能模块

### 用户模块
- 用户注册和登录
- 用户信息管理
- 权限控制

### 仓库模块
- 仓库的CRUD操作
- 协作者管理
- 仓库访问控制

### 文件模块
- 文件上传和存储
- 文件结构化处理
- 文件导出功能

### 聊天模块
- AI对话功能
- 聊天历史记录
- 对话内容管理

## 设计原则
1. 关注点分离：每个模块负责特定的功能
2. 依赖注入：通过依赖注入实现模块解耦
3. 单一职责：每个类和函数只负责一个特定任务
4. 接口隔离：通过接口定义模块间的交互

## 开发建议
1. 遵循分层架构，避免跨层调用
2. 使用依赖注入管理服务实例
3. 保持代码的可测试性
4. 统一错误处理和日志记录
5. 注重代码复用和模块化

- repo

  - repoID

  - ownerId
  - co-userIdList
  - FileIdList
  - StructureFileIDList

- User:

  - UserId
  - name
  - password
  - RepoIdList
  - ChatHistoryID

- ChatHistory

  - ChatHistoryID
    - TextList(sayer, txt)

- File:

  - FileID
  - Content

- StructureFile

  - StructureFileID
  - excel
  - json



```python
@post()
def upload():
    
    # 数据库存好filelist
    
    {
        new thread : slist = process(filelist)
    
    	# 数据库存好slist
    
    	# 给客户端返回信息
    }
    
    return succ

def process(filelist):
    # 移动到source
    
    # 调用
    
    # 拿到structure
    
    # 清空文件夹
    
    return StructureFileList

# 预览repo
@get()
def getRepoDescriptionList(UserID):
    return list<RepoName>

@get, post, delete, update
("user/{userid}/Repo/{RepoID}")

# 预览文件列表
@get()
def getFileDescriptionLIst(RepoID):
    return list


@post()
def chat(text):
    # 调用API
    
    # 每次存chat txt
    
    return response


# 预览chathistory
@get()
def getChatHistoryDescriptionList(UserID):
    
    return list


@get()
def getChat(UserID, historyID):
    # historyID
    return list<txt>
    
```

