# Backend 2.0

这是项目的重构版本，采用更清晰的分层架构。

## 目录结构
```
backend_2/
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
│       ├── base.py     # 基础仓库类
│       ├── user.py     # 用户数据访问
│       ├── repo.py     # 仓库数据访问
│       ├── file.py     # 文件数据访问
│       └── chat.py     # 聊天数据访问
├── utils/              # 工具函数
│   ├── __init__.py
│   └── helpers.py     # 通用辅助函数
└── DataStructuring/   # 文件处理模块
    └── DataStructuring/
        ├── main.py    # 文件处理主逻辑
        ├── SourceData/ # 源文件目录
        └── TargetData/ # 处理后文件目录
```

## 重构说明

1. 将原有的models.py拆分为独立的模型文件
2. 将routers.py拆分为不同的路由端点文件
3. 添加服务层处理业务逻辑
4. 添加数据访问层处理数据库操作
5. 保留原有的DataStructuring模块
6. 添加配置管理和错误处理

## 迁移步骤

1. 创建新的目录结构
2. 迁移现有模型到models/目录
3. 迁移路由到api/endpoints/目录
4. 实现服务层和数据访问层
5. 配置数据库连接
6. 迁移文件处理逻辑
7. 添加认证和错误处理 