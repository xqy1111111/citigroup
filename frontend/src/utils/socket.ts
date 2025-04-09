import { useCurrentRepoStore } from './state';
import { useUserStore } from './state';

class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout = 3000;

  connect(repoId: string) {
    try {
      const userStore = useUserStore();
      const token = userStore.getToken();
      
      this.socket = new WebSocket(`ws://localhost:8000/ws/${repoId}?token=${token}`);

      this.socket.onopen = () => {
        console.log('WebSocket连接已建立');
        this.reconnectAttempts = 0;
      };

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };

      this.socket.onclose = () => {
        console.log('WebSocket连接已关闭');
        this.attemptReconnect(repoId);
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket错误:', error);
      };
    } catch (error) {
      console.error('建立WebSocket连接时出错:', error);
    }
  }

  private handleMessage(data: any) {
    const currentRepo = useCurrentRepoStore();
    console.log('收到WebSocket消息:', data);
    
    switch (data.type) {
      case 'FILE_UPLOADED':
        console.log('处理FILE_UPLOADED消息:', data);
        if (data.repo_id === currentRepo.id && Array.isArray(data.files)) {
          console.log('更新文件列表:', data.files);
          currentRepo.updateCurrentRepoFiles(data.files);
        }
        break;
      case 'FILE_STATUS_CHANGED':
        console.log('处理FILE_STATUS_CHANGED消息:', data);
        if (data.repo_id === currentRepo.id) {
          const fileIndex = currentRepo.files.findIndex(f => f.file_id === data.file_id);
          if (fileIndex !== -1) {
            const updatedFiles = [...currentRepo.files];
            updatedFiles[fileIndex] = {
              ...updatedFiles[fileIndex],
              status: data.status
            };
            console.log('更新文件状态:', updatedFiles);
            currentRepo.updateCurrentRepoFiles(updatedFiles);
          }
        }
        break;
      case 'FILE_PROCESSING_COMPLETE':
        console.log('处理FILE_PROCESSING_COMPLETE消息:', data);
        if (data.repo_id === currentRepo.id) {
          currentRepo.updateCurrentRepoResults(data.results);
        }
        break;
    }
  }

  private attemptReconnect(repoId: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`尝试重新连接... 第${this.reconnectAttempts}次`);
      setTimeout(() => this.connect(repoId), this.reconnectTimeout);
    }
  }

  sendMessage(type: string, data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, ...data }));
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

export const wsService = new WebSocketService(); 