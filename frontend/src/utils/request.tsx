import axios from "axios";

// 使用相对路径，将通过代理转发到后端
export const API_BASE_URL = '';

export const request = axios.create(
  {
    baseURL: API_BASE_URL,
    headers: {
      'accept': 'application/json',
      'Content-Type': 'application/json'
    },
    // 允许跨域携带cookie
    withCredentials: true
  }
);

request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      // 服务器返回错误信息
      const errorMessage = error.response.data.detail || '请求失败';
      throw new Error(errorMessage);
    } else if (error.request) {
      // 请求发出但没有收到响应
      throw new Error('无法连接到服务器');
    } else {
      // 请求配置错误
      throw new Error('请求配置错误');
    }
  }
); 
