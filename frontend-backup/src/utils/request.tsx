import axios from "axios";
import { config } from "../config/api";

export const request = axios.create(
  {
    baseURL: config.baseUrl,
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
