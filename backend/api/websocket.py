from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from jose import jwt
from core.security import SECRET_KEY, ALGORITHM  # 导入JWT相关的配置
from api.repo import get_repo  # 导入获取仓库信息的函数

class ConnectionManager:
    def __init__(self):
        # 存储所有活跃的WebSocket连接
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, repo_id: str):
        await websocket.accept()
        if repo_id not in self.active_connections:
            self.active_connections[repo_id] = []
        self.active_connections[repo_id].append(websocket)

    def disconnect(self, websocket: WebSocket, repo_id: str):
        if repo_id in self.active_connections:
            self.active_connections[repo_id].remove(websocket)
            if not self.active_connections[repo_id]:
                del self.active_connections[repo_id]

    async def broadcast_to_repo(self, repo_id: str, message: dict):
        if repo_id in self.active_connections:
            for connection in self.active_connections[repo_id]:
                try:
                    await connection.send_json(message)
                except WebSocketDisconnect:
                    await self.disconnect(connection, repo_id)

manager = ConnectionManager()

async def handle_websocket(websocket: WebSocket, repo_id: str, token: str = None):
    try:
        # 验证token
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return
            
        try:
            # 验证token并获取用户ID
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=4003, reason="Invalid authentication token")
                return
        except Exception as e:
            await websocket.close(code=4003, reason="Invalid authentication token")
            return

        await manager.connect(websocket, repo_id)
        
        while True:
            try:
                # 等待接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 根据消息类型处理
                if message['type'] == 'FILE_UPLOADED':
                    # 获取最新的仓库信息
                    repo_response = await get_repo(repo_id)
                    # 广播文件上传成功消息
                    await manager.broadcast_to_repo(repo_id, {
                        'type': 'FILE_UPLOADED',
                        'repo_id': repo_id,
                        'files': repo_response.files  # 直接使用RepoResponse对象的files属性
                    })
                elif message['type'] == 'FILE_STATUS_CHANGED':
                    # 广播文件状态变更消息
                    await manager.broadcast_to_repo(repo_id, {
                        'type': 'FILE_STATUS_CHANGED',
                        'repo_id': repo_id,
                        'file_id': message.get('file_id'),
                        'status': message.get('status')
                    })
                
            except WebSocketDisconnect:
                manager.disconnect(websocket, repo_id)
                break
            except Exception as e:
                print(f"处理WebSocket消息时出错: {str(e)}")
                print(f"错误详情: {e.__class__.__name__}")  # 打印错误类型
                continue
                
    except Exception as e:
        print(f"WebSocket连接出错: {str(e)}")
        manager.disconnect(websocket, repo_id) 