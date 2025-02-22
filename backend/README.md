# NOTICE
本文主要由ai基于我们的代码生成，由于时间较晚未来得及修改，api部分以localhost:8000/docs为准，这是fastapi提供的一个util，非常好用

如果遇到任何问题请在群里提出

目前只是一个初版，部分内容还需要完善 :)

# 项目运行准备

## 1. 安装依赖：
```bash
pip install -r requirements.txt
```

## 2. 安装ffmpeg：
> 参考连接：https://blog.csdn.net/csdn_yudong/article/details/129182648

## 3. 安装ollama，并且需要pull ollama 的特定模型
> 参考连接：https://blog.csdn.net/2301_81940605/article/details/145512685  
> 实际使用的模型是：https://ollama.org.cn/wangshenzhi/llama3-8b-chinese-chat-ollama-q4:v1

## 4. 安装MongoDB
> 参考连接：https://blog.csdn.net/LiDaode/article/details/133241186

## 5. 运行项目
```bash
uvicorn main:app --reload
```
然后可以在`localhost:8000/docs`访问项目，同时也可以进行API测试

# 用户相关 API 文档

## 基础信息
- **API 前缀**：`/users`
- **请求格式**：JSON
- **响应格式**：JSON
- **认证方式**：部分接口需要提供用户认证信息

---

## 1. 创建用户

### **接口**
**POST** `/users/`

### **请求参数**
```json
{
  "username": "example_user",
  "email": "user@example.com",
  "password": "securepassword",
  "profile_picture": "https://example.com/profile.jpg"
}
```
> **说明**：
> - `username` (string) - 必填，用户名，不可为空字符串
> - `email` (string) - 必填，用户邮箱，需符合 Email 规范
> - `password` (string) - 必填，用户密码
> - `profile_picture` (string, optional) - 选填，用户头像的 URL

### **响应**
#### **成功**
```json
{
  "id": "65dbf5b67a2f4d8e8b4c9f9d",
  "username": "example_user",
  "email": "user@example.com",
  "profile_picture": "https://example.com/profile.jpg",
  "repos": [],
  "collaborations": []
}
```
> **说明**：
> - `id` (string) - MongoDB 生成的用户 ID
> - `repos` (list) - 该用户拥有的仓库 ID 列表
> - `collaborations` (list) - 该用户参与的仓库 ID 列表

#### **失败**
- **HTTP 400**: 请求参数错误
- **HTTP 500**: 服务器错误

---

## 2. 用户认证（登录）

### **接口**
**POST** `/users/authenticate/`

### **请求参数**
```json
{
  "username_or_email": "user@example.com",
  "password": "securepassword"
}
```
> **说明**：
> - `username_or_email` (string) - 用户名或邮箱，支持使用用户名或邮箱进行登录
> - `password` (string) - 用户密码

### **响应**
#### **成功**
```json
{
  "user_id": "65dbf5b67a2f4d8e8b4c9f9d",
  "message": "Authentication successful"
}
```
> **说明**：
> - `user_id` (string) - MongoDB 生成的用户 ID
> - `message` (string) - 默认返回 `"Authentication successful"`

#### **失败**
- **HTTP 401**: 认证失败，用户名或密码错误
- **HTTP 500**: 服务器错误

---

## 3. 获取用户信息

### **接口**
**GET** `/users/{user_id}`

### **路径参数**
| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|--------|------|
| `user_id` | string | 是 | 用户的 MongoDB `_id` |

### **示例请求**
```http
GET /users/65dbf5b67a2f4d8e8b4c9f9d
```

### **响应**
#### **成功**
```json
{
  "id": "65dbf5b67a2f4d8e8b4c9f9d",
  "username": "example_user",
  "email": "user@example.com",
  "profile_picture": "https://example.com/profile.jpg",
  "repos": ["603f9c39e3d9b341d8c7d6b2"],
  "collaborations": ["60f1c9a6d4f7e8144d2c9f45"]
}
```
> **说明**：
> - `id` (string) - MongoDB 生成的用户 ID
> - `username` (string) - 用户名
> - `email` (string) - 用户邮箱
> - `profile_picture` (string, optional) - 头像 URL
> - `repos` (list) - 该用户拥有的仓库 ID 列表
> - `collaborations` (list) - 该用户参与的仓库 ID 列表

#### **失败**
- **HTTP 404**: 用户不存在
- **HTTP 500**: 服务器错误

---

## 额外说明
1. **密码存储**：密码不会明文存储，而是经过加密处理。
2. **错误处理**：
   - **请求参数不合法**：返回 HTTP 400，包含错误信息
   - **未找到资源**：返回 HTTP 404
   - **服务器错误**：返回 HTTP 500
3. **用户身份认证**：
   - `authenticate/` 登录后，前端应存储 `user_id` 以用于后续 API 调用。


# 仓库相关 API 文档

## 基础信息
- **API 前缀**：`/repos`
- **请求格式**：JSON
- **响应格式**：JSON
- **认证方式**：部分接口需要提供用户认证信息

---

## 1. 创建仓库

### **接口**
**POST** `/repos/`

### **请求参数**
```json
{
  "name": "example_repo",
  "desc": "This is a test repository"
}
```
> **说明**：
> - `name` (string) - 必填，仓库名称，不可为空字符串
> - `desc` (string) - 必填，仓库描述
> - **Query 参数**: `owner_id` (string) - 必填，仓库所有者的用户 ID

### **示例请求**
```http
POST /repos/?owner_id=65dbf5b67a2f4d8e8b4c9f9d
```
```json
{
  "name": "example_repo",
  "desc": "This is a test repository"
}
```

### **响应**
#### **成功**
```json
{
  "id": "60f1c9a6d4f7e8144d2c9f45",
  "name": "example_repo",
  "desc": "This is a test repository",
  "owner_id": "65dbf5b67a2f4d8e8b4c9f9d",
  "collaborators": [],
  "files": [],
  "results": []
}
```
> **说明**：
> - `id` (string) - MongoDB 生成的仓库 ID
> - `owner_id` (string) - 仓库拥有者的用户 ID
> - `collaborators` (list) - 该仓库的协作者 ID 列表
> - `files` (list) - 该仓库内的文件 ID 列表
> - `results` (list) - 该仓库的处理结果 ID 列表

#### **失败**
- **HTTP 400**: 创建失败
- **HTTP 500**: 服务器错误

---

## 2. 获取仓库信息

### **接口**
**GET** `/repos/{repo_id}`

### **路径参数**
| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|--------|------|
| `repo_id` | string | 是 | 仓库的 MongoDB `_id` |

### **示例请求**
```http
GET /repos/60f1c9a6d4f7e8144d2c9f45
```

### **响应**
#### **成功**
```json
{
  "id": "60f1c9a6d4f7e8144d2c9f45",
  "name": "example_repo",
  "desc": "This is a test repository",
  "owner_id": "65dbf5b67a2f4d8e8b4c9f9d",
  "collaborators": ["603f9c39e3d9b341d8c7d6b2"],
  "files": ["5f1d7f9b2f9b3c001cc3e3a7"],
  "results": ["60d2a1c9d7f8e9144d2b9f12"]
}
```

#### **失败**
- **HTTP 404**: 仓库不存在
- **HTTP 500**: 服务器错误

---

## 3. 更新仓库名称

### **接口**
**PUT** `/repos/{repo_id}/name`

### **请求参数**
```json
{
  "new_name": "updated_repo_name"
}
```
> **说明**：
> - `new_name` (string) - 必填，新仓库名称

### **示例请求**
```http
PUT /repos/60f1c9a6d4f7e8144d2c9f45/name
```
```json
{
  "new_name": "updated_repo_name"
}
```

### **响应**
#### **成功**
```json
"Name updated successfully"
```

#### **失败**
- **HTTP 400**: 更新失败
- **HTTP 500**: 服务器错误

---

## 4. 更新仓库描述

### **接口**
**PUT** `/repos/{repo_id}/desc`

### **请求参数**
```json
{
  "new_desc": "Updated description for the repository"
}
```
> **说明**：
> - `new_desc` (string) - 必填，新仓库描述

### **示例请求**
```http
PUT /repos/60f1c9a6d4f7e8144d2c9f45/desc
```
```json
{
  "new_desc": "Updated description for the repository"
}
```

### **响应**
#### **成功**
```json
"Description updated successfully"
```

#### **失败**
- **HTTP 400**: 更新失败
- **HTTP 500**: 服务器错误

---

## 5. 删除仓库

### **接口**
**DELETE** `/repos/{repo_id}`

### **示例请求**
```http
DELETE /repos/60f1c9a6d4f7e8144d2c9f45
```

### **响应**
#### **成功**
```json
"Repo deleted successfully"
```

#### **失败**
- **HTTP 400**: 删除失败
- **HTTP 500**: 服务器错误

---

## 6. 添加协作者

### **接口**
**POST** `/repos/{repo_id}/collaborators`

### **请求参数**
```json
{
  "collaborator_id": "603f9c39e3d9b341d8c7d6b2"
}
```
> **说明**：
> - `collaborator_id` (string) - 必填，要添加的协作者用户 ID

### **示例请求**
```http
POST /repos/60f1c9a6d4f7e8144d2c9f45/collaborators
```
```json
{
  "collaborator_id": "603f9c39e3d9b341d8c7d6b2"
}
```

### **响应**
#### **成功**
```json
"Collaborator added successfully"
```

#### **失败**
- **HTTP 400**: 添加失败
- **HTTP 500**: 服务器错误

---

## 额外说明
1. **仓库数据存储**：
   - `collaborators`、`files`、`results` 字段均存储为对象 ID 列表，所有 ID 均为字符串格式。
2. **错误处理**：
   - **请求参数不合法**：返回 HTTP 400，包含错误信息
   - **未找到资源**：返回 HTTP 404
   - **服务器错误**：返回 HTTP 500
3. **权限管理**：
   - 仅 `owner_id` 可修改 `name`、`desc`，以及删除仓库。
   - `collaborators` 可以查看仓库，但不能修改仓库基本信息。
   
# 文件相关 API 文档

## 基础信息
- **API 前缀**：`/files`
- **请求格式**：JSON / multipart-form-data
- **响应格式**：JSON / 文件流
- **认证方式**：部分接口需要提供用户认证信息

---

## 1. 上传文件

### **接口**
**POST** `/files/upload`

### **请求参数**
- **Query 参数**：
  | 参数名 | 类型 | 是否必填 | 说明 |
  |--------|------|--------|------|
  | `repo_id` | string | 是 | 目标仓库的 ID |
  | `source` | bool | 否 | 是否存入 `repo.files`（默认 `True`），`False` 则存入 `repo.results` |

- **Body 参数**（multipart-form-data）：
  | 参数名 | 类型 | 是否必填 | 说明 |
  |--------|------|--------|------|
  | `cur_file` | 文件 | 是 | 需要上传的文件 |

### **示例请求**
```http
POST /files/upload?repo_id=60f1c9a6d4f7e8144d2c9f45&source=true
Content-Type: multipart/form-data
```

### **响应**
#### **成功**
```json
{
  "file_id": "65f9a6c3d2b8a912b3f7d6c9",
  "filename": "example.txt",
  "size": 12345,
  "upload_date": "2024-02-22T12:34:56",
  "status": "pending"
}
```
> **说明**：
> - `file_id` (string) - 上传文件的唯一 ID
> - `filename` (string) - 文件名
> - `size` (int) - 文件大小（单位：字节）
> - `upload_date` (datetime) - 上传时间
> - `status` (string) - 文件状态（默认为 `pending`）

#### **失败**
- **HTTP 400**: 上传失败
- **HTTP 404**: 仓库不存在
- **HTTP 500**: 服务器错误

---

## 2. 获取文件元数据

### **接口**
**GET** `/files/{file_id}`

### **Query 参数**
| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|--------|------|
| `repo_id` | string | 是 | 目标仓库的 ID |
| `source` | bool | 否 | 是否从 `repo.files` 获取（默认 `True`），`False` 则从 `repo.results` 获取 |

### **示例请求**
```http
GET /files/65f9a6c3d2b8a912b3f7d6c9?repo_id=60f1c9a6d4f7e8144d2c9f45&source=true
```

### **响应**
#### **成功**
```json
{
  "file_id": "65f9a6c3d2b8a912b3f7d6c9",
  "filename": "example.txt",
  "size": 12345,
  "upload_date": "2024-02-22T12:34:56",
  "status": "complete"
}
```

#### **失败**
- **HTTP 404**: 文件不存在
- **HTTP 500**: 服务器错误

---

## 3. 下载文件

### **接口**
**GET** `/files/{file_id}/download`

### **示例请求**
```http
GET /files/65f9a6c3d2b8a912b3f7d6c9/download
```

### **响应**
#### **成功**
- **文件流**，文件会作为 `attachment` 下载。

#### **失败**
- **HTTP 404**: 文件不存在
- **HTTP 500**: 服务器错误

---

## 4. 删除文件

### **接口**
**DELETE** `/files/{file_id}`

### **示例请求**
```http
DELETE /files/65f9a6c3d2b8a912b3f7d6c9
```

### **响应**
#### **成功**
```json
{
  "detail": "File deleted successfully"
}
```

#### **失败**
- **HTTP 404**: 文件不存在
- **HTTP 500**: 服务器错误

---

## 5. 更新文件状态

### **接口**
**PUT** `/files/{file_id}`

### **Query 参数**
| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|--------|------|
| `repo_id` | string | 是 | 目标仓库的 ID |
| `source` | bool | 否 | 是否更新 `repo.files`（默认 `True`），`False` 则更新 `repo.results` |

### **Body 参数**
```json
{
  "new_status": "complete"
}
```
> **说明**：
> - `new_status` (string) - 新的文件状态，例如 `"complete"` 或 `"processing"`

### **示例请求**
```http
PUT /files/65f9a6c3d2b8a912b3f7d6c9?repo_id=60f1c9a6d4f7e8144d2c9f45&source=true
```
```json
{
  "new_status": "complete"
}
```

### **响应**
#### **成功**
```json
"File 65f9a6c3d2b8a912b3f7d6c9 status updated to complete"
```

#### **失败**
- **HTTP 404**: 文件不存在
- **HTTP 500**: 服务器错误

---

## 额外说明
1. **文件存储**：
   - 文件存储在 **GridFS**，文件元数据存储在 MongoDB。
   - `repo.files` 和 `repo.results` 是不同的文件集合，`source=True` 代表普通文件，`source=False` 代表处理结果。
2. **错误处理**：
   - **请求参数不合法**：返回 HTTP 400，包含错误信息
   - **未找到资源**：返回 HTTP 404
   - **服务器错误**：返回 HTTP 500
3. **文件状态管理**：
   - 文件默认状态为 `"pending"`。
   - 可以手动更新状态，如 `"processing"`、`"complete"` 以反映处理进度。

---


# 聊天相关 API 文档

## 基础信息
- **API 前缀**：`/chat`
- **请求格式**：JSON / multipart-form-data
- **响应格式**：JSON
- **认证方式**：部分接口需要提供用户认证信息

---

## 1. 发送聊天消息

### **接口**
**POST** `/chat`

### **请求参数**
```json
{
  "message": "请分析一下这份金融合同的风险"
}
```
> **说明**：
> - `message` (string) - 必填，用户发送的聊天信息

### **示例请求**
```http
POST /chat
Content-Type: application/json
```
```json
{
  "message": "请分析一下这份金融合同的风险"
}
```

### **响应**
#### **成功**
```json
{
  "sayer": "assistant",
  "text": "根据您的输入，这份合同存在潜在的风险，请进一步核查交易主体信息。",
  "timestamp": "2024-02-22T12:34:56"
}
```
> **说明**：
> - `sayer` (string) - 说话人，值为 `"assistant"` 或 `"user"`
> - `text` (string) - AI 返回的回答
> - `timestamp` (datetime) - 发送时间

#### **失败**
- **HTTP 500**: 服务器错误

---

## 2. 发送带文件的聊天消息

### **接口**
**POST** `/chat/with-file`

### **请求参数**
- **Query 参数**：
  | 参数名 | 类型 | 是否必填 | 说明 |
  |--------|------|--------|------|
  | `message` | string | 是 | 用户的聊天内容 |

- **Body 参数**（multipart-form-data）：
  | 参数名 | 类型 | 是否必填 | 说明 |
  |--------|------|--------|------|
  | `file` | 文件 | 是 | 需要上传的 Excel 文件 |

### **示例请求**
```http
POST /chat/with-file?message=请分析这份合同的风险
Content-Type: multipart/form-data
```

### **响应**
#### **成功**
```json
{
  "sayer": "assistant",
  "text": "文件分析结果：风险评估为 30%，建议进一步核查交易主体信息。",
  "timestamp": "2024-02-22T12:34:56"
}
```

#### **失败**
- **HTTP 400**: 文件上传失败
- **HTTP 404**: 处理过程中文件丢失
- **HTTP 500**: 服务器错误

---

## 3. 获取用户聊天历史列表（暂未实现）

### **接口**
**GET** `/chat/history/{user_id}`

### **路径参数**
| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|--------|------|
| `user_id` | string | 是 | 用户的 MongoDB `_id` |

### **示例请求**
```http
GET /chat/history/65dbf5b67a2f4d8e8b4c9f9d
```

### **响应**
#### **成功**
```json
[]
```
> **说明**：
> - 当前 API 暂未实现，返回空数组

---

## 4. 获取特定聊天历史的消息列表（暂未实现）

### **接口**
**GET** `/chat/history/{user_id}/{history_id}/messages`

### **路径参数**
| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|--------|------|
| `user_id` | string | 是 | 用户的 MongoDB `_id` |
| `history_id` | string | 是 | 聊天历史 ID |

### **示例请求**
```http
GET /chat/history/65dbf5b67a2f4d8e8b4c9f9d/60f1c9a6d4f7e8144d2c9f45/messages
```

### **响应**
#### **成功**
```json
[]
```
> **说明**：
> - 当前 API 暂未实现，返回空数组

---

## 5. 删除特定聊天历史（暂未实现）

### **接口**
**DELETE** `/chat/history/{user_id}/{history_id}`

### **路径参数**
| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|--------|------|
| `user_id` | string | 是 | 用户的 MongoDB `_id` |
| `history_id` | string | 是 | 聊天历史 ID |

### **示例请求**
```http
DELETE /chat/history/65dbf5b67a2f4d8e8b4c9f9d/60f1c9a6d4f7e8144d2c9f45
```

### **响应**
#### **成功**
```json
{
  "detail": "Chat history deleted successfully"
}
```

---

## 额外说明
1. **聊天模型**：
   - `chat/` 为普通聊天接口，适用于用户直接发送文本。
   - `chat/with-file` 适用于用户上传 Excel 文件，并让 AI 进行金融风险分析。
2. **错误处理**：
   - **请求参数不合法**：返回 HTTP 400，包含错误信息
   - **未找到资源**：返回 HTTP 404
   - **服务器错误**：返回 HTTP 500
3. **聊天历史管理**：
   - 目前 `/history` 相关接口尚未实现，如有需要，可提供相应代码继续完善。

---

# 文件处理 API 文档

## 基础信息
- **API 前缀**：`/process`
- **请求格式**：JSON
- **响应格式**：JSON
- **认证方式**：部分接口需要提供用户认证信息

---

## 1. 处理文件并转换为 JSON

### **接口**
**POST** `/process/{file_id}/process`

### **路径参数**
| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|--------|------|
| `file_id` | string | 是 | 要处理的文件 ID |

### **示例请求**
```http
POST /process/65f9a6c3d2b8a912b3f7d6c9/process
```

### **响应**
#### **成功**
```json
{
  "document_title": "Financial Report",
  "sections": [
    {
      "title": "Introduction",
      "content": "This is the introduction section of the report."
    },
    {
      "title": "Risk Analysis",
      "content": "This section discusses financial risks and fraud detection."
    }
  ],
  "processed_at": "2024-02-22T12:34:56"
}
```
> **说明**：
> - `document_title` (string) - 解析后的文档标题
> - `sections` (list) - 解析出的文档章节内容，每个元素包含 `title`（章节标题）和 `content`（章节内容）
> - `processed_at` (datetime) - 处理完成时间

#### **失败**
- **HTTP 404**: 文件未找到
- **HTTP 500**: 服务器错误

---

## 额外说明
1. **文件处理流程**：
   - **下载文件**：从数据库中获取 `file_id` 对应的文件内容。
   - **存入 `SourceData` 目录**：清空目录，写入文件。
   - **执行 `main_process.main_process()` 进行解析**：将文件内容结构化处理。
   - **转换为 JSON**：调用 `target_to_json.process_target_to_json()` 生成 JSON 数据。
   - **返回 JSON 数据**：最终返回解析后的 JSON 文件内容。

2. **错误处理**：
   - **文件不存在**：返回 HTTP 404
   - **JSON 解析失败**：返回 HTTP 500

---
