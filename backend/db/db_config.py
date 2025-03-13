"""
数据库配置模块

这个模块包含MongoDB数据库的连接配置。
将数据库连接信息集中在一个文件中有助于：
1. 轻松更改连接设置而不影响其他代码
2. 避免在代码库中重复硬编码连接字符串
3. 在部署不同环境(开发、测试、生产)时方便配置

MongoDB连接字符串格式:
mongodb://[username:password@]host[:port][/database]

生产环境最佳实践:
- 使用环境变量存储连接信息，而不是硬编码
- 启用身份验证并使用强密码
- 限制IP访问范围
- 使用SSL/TLS加密连接
"""
import os

# MongoDB连接URL
# 开发环境使用本地MongoDB实例
# 生产环境应使用环境变量配置，例如: os.getenv("MONGO_URL", "默认值")
DB_URL = "mongodb://localhost:27017/"
