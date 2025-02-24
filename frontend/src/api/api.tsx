export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  
  // API endpoints
  ENDPOINTS: {
    PROCESS: (fileId: string) => `/process/${fileId}/process`,
    // ... 其他端点
  }
};