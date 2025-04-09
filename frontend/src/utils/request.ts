import axios from "axios";
import {router} from "../router";
import {useUserStore} from "./state.ts";
import { ElMessage } from 'element-plus';

/**
 * Axios实例配置
 * 创建一个具有预设配置的axios实例，用于处理所有HTTP请求
 */
export const request = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    timeout: 10000,
    withCredentials: true
});

/**
 * 统一错误处理函数
 * 根据不同的HTTP状态码处理错误，并向用户显示友好的错误消息
 * @param error - Axios错误对象
 * @returns Promise.reject - 返回被拒绝的Promise以便调用者可以进一步处理错误
 */
const handleRequestError = (error: any) => {
    const response = error.response;

    // 网络错误或服务器未响应
    if (!response) {
        ElMessage.error('网络错误，请检查您的连接');
        return Promise.reject(error);
    }

    // 根据HTTP状态码处理不同类型的错误
    switch (response.status) {
        case 400:
            // 请求参数错误
            ElMessage.error(response.data?.detail || '请求参数错误');
            break;
        case 401:
            // [已修改] 未授权，用户需要登录
            // 只有在不是登录/注册页面时才显示消息
            if (router.currentRoute.value.path !== '/login' && 
                router.currentRoute.value.path !== '/register') {
                ElMessage.error('登录已过期，请重新登录');
            }
            
            // 清除用户信息
            const userStore = useUserStore();
            userStore.clearUserInfo();
            
            // 记录当前路径用于登录后重定向
            const currentPath = router.currentRoute.value.fullPath;
            if (currentPath !== '/login' && currentPath !== '/register') {
                router.push({
                    path: '/login',
                    query: { redirect: currentPath }
                });
            }
            break;
        case 403:
            // 禁止访问，权限不足
            ElMessage.error('您没有权限执行此操作');
            break;
        case 404:
            // 资源不存在
            ElMessage.error('请求的资源不存在');
            break;
        case 409:
            // 资源冲突，通常是重复记录
            ElMessage.error(response.data?.detail || '请求冲突，可能存在重复数据');
            break;
        case 422:
            // 数据验证错误，通常来自Pydantic验证
            if (response.data?.detail && Array.isArray(response.data.detail)) {
                const errors = response.data.detail.map((err: any) => {
                    return `${err.loc.join('.')}：${err.msg}`;
                }).join('; ');
                ElMessage.error(`数据验证错误: ${errors}`);
            } else {
                ElMessage.error(response.data?.detail || '数据验证错误');
            }
            break;
        case 429:
            // 请求频率限制
            ElMessage.error('请求过于频繁，请稍后再试');
            break;
        case 500:
        case 502:
        case 503:
        case 504:
            // 服务器错误
            ElMessage.error('服务器错误，请稍后再试');
            break;
        default:
            // 其他未处理的错误
            ElMessage.error(response.data?.detail || '请求失败');
    }

    return Promise.reject(error);
};

/**
 * 请求拦截器
 * [已修改] 确保每次请求前都从当前标签页的sessionStorage重新获取最新令牌
 */
request.interceptors.request.use(
    config => {
        const userStore = useUserStore();
        
        // [已修改] 每次请求前都强制重新加载用户数据，确保使用当前标签页的正确令牌
        userStore.localStorageUserData();
        
        const token = userStore.getToken();
        
        // 添加认证令牌到请求头
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
            console.log('[已修改] 请求使用当前标签页的令牌:', config.url);
        } else {
            console.log('[已修改] 请求没有令牌（当前标签页未登录）:', config.url);
        }

        return config;
    }, 
    error => {
        console.error('请求拦截器错误:', error);
        return Promise.reject(error);
    }
);

/**
 * 响应拦截器
 * [已修改] 简化响应处理逻辑，刷新令牌时使用sessionStorage
 */
request.interceptors.response.use(
    response => {
        // 直接返回成功的响应
        return response;
    }, 
    async error => {
        const originalRequest = error.config;
        const userStore = useUserStore();
        
        // [已修改] 处理401错误（未授权）并尝试刷新令牌
        if (error.response?.status === 401 && 
            !originalRequest._retry && 
            userStore.getRefreshToken()) {
                
            originalRequest._retry = true;
            
            try {
                // 尝试使用刷新令牌获取新的访问令牌
                const refreshToken = userStore.getRefreshToken();
                const response = await axios.post(
                    `${request.defaults.baseURL}/auth/refresh`,
                    { refresh_token: refreshToken }
                );
                
                if (response.data.access_token) {
                    // [已修改] 更新存储中的令牌（使用sessionStorage）
                    userStore.setToken(
                        response.data.access_token, 
                        response.data.refresh_token || refreshToken
                    );
                    
                    // 使用新令牌重试原始请求
                    originalRequest.headers['Authorization'] = `Bearer ${response.data.access_token}`;
                    return axios(originalRequest);
                }
            } catch (refreshError) {
                console.error('令牌刷新失败:', refreshError);
                // 刷新令牌失败，清除用户信息并重定向到登录页面
                userStore.clearUserInfo();
                
                // 获取当前路径用于登录后重定向
                const currentPath = router.currentRoute.value.fullPath;
                if (currentPath !== '/login' && currentPath !== '/register') {
                    router.push({
                        path: '/login',
                        query: { redirect: currentPath }
                    });
                }
            }
        }
        
        // 处理其他错误
        return handleRequestError(error);
    }
);


