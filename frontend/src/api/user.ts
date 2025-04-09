import { request } from '../utils/request';
import { useUserStore } from '../utils/state';
import { router } from '../router';
import { ElMessage } from 'element-plus';

/**
 * 登录数据接口
 * 定义登录请求所需的用户数据结构
 */
export interface loginData {
    username: string;  // 用户名
    email: string;     // 电子邮件
    password: string;  // 密码
    profile_picture?: string;  // 可选的头像URL
}

/**
 * 认证响应接口
 * 定义后端认证API返回的数据结构
 */
export interface authResponse {
    access_token: string;   // JWT访问令牌
    refresh_token: string;  // JWT刷新令牌
    token_type: string;     // 令牌类型，通常为"bearer"
    user_id?: string;       // 可选的用户ID
    message?: string;       // 可选的响应消息
}

/**
 * 用户数据接口
 * 定义用户基本信息的数据结构
 */
export interface userData {
    id: string;              // 用户唯一标识符
    username: string;        // 用户名
    email: string;           // 电子邮件
    profile_picture: string; // 头像URL
    repos: string[];         // 用户拥有的仓库ID列表
    collaborations: string[]; // 用户协作的仓库ID列表
}

/**
 * 用户登录API
 * [已修改] 确保登录状态只存储在当前标签页的sessionStorage中
 * [已修改] 成功获取用户信息后返回Promise，由调用组件处理跳转
 * @param data - 包含用户名/邮箱和密码的登录数据
 * @returns Promise - 返回包含认证响应的Promise
 */
export const userLogin = (data: loginData) => {
    const userStore = useUserStore();
    
    return request.post('/auth/token', {
        username: data.username || data.email,
        password: data.password
    }, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        transformRequest: [(data) => {
            // 将数据转换为表单格式
            const formData = new URLSearchParams();
            for (const key in data) {
                formData.append(key, data[key]);
            }
            return formData.toString();
        }],
        validateStatus: (status) => status >= 200 && status < 300
    }).then(response => {
        // 登录成功，保存令牌到用户存储
        if (response.data.access_token) {
            // 确保清除旧的令牌和用户信息
            userStore.clearUserInfo();
            
            // [已修改] 设置新的令牌（存储在sessionStorage中）
            userStore.setToken(
                response.data.access_token,
                response.data.refresh_token || '' // 确保即使没有refresh_token也不会传入undefined
            );
            
            console.log('[已修改] 登录成功，令牌已保存到当前标签页会话');
            
            // [已修改] 登录成功后获取用户信息
            return getCurrentUser().then(() => {
                console.log('[已修改] 用户信息获取成功，由组件处理跳转');
                
                // 返回响应以便调用组件处理后续逻辑（如跳转）
                return response;
            });
        }
        
        return response;
    });
}

/**
 * 刷新访问令牌API
 * 使用刷新令牌获取新的访问令牌
 * @returns Promise - 返回包含新令牌的Promise
 */
export const refreshToken = () => {
    const userStore = useUserStore();
    const refreshToken = userStore.getRefreshToken();
    
    if (!refreshToken) {
        return Promise.reject(new Error('无刷新令牌可用'));
    }
    
    return request.post('/auth/refresh', {
        refresh_token: refreshToken
    }).then(response => {
        if (response.data.access_token) {
            userStore.setToken(
                response.data.access_token,
                response.data.refresh_token || refreshToken
            );
        }
        return response;
    });
}

/**
 * 获取当前登录用户信息API
 * [已修改] 简化认证检查，依赖请求拦截器处理未授权情况
 * @returns Promise - 返回包含用户数据的Promise
 */
export const getCurrentUser = () => {
    // [已修改] 不再在这里检查令牌，让请求拦截器处理认证逻辑
    // 这样可以保持前后端一致的认证策略
    return request.get('/users/me')
        .then(response => {
            // 获取成功后更新用户存储
            if (response?.data) {
                const userStore = useUserStore();
                userStore.setUserInfo(response.data);
            }
            return response;
        });
    // [已修改] 移除额外的错误处理，让请求拦截器统一处理错误
}

/**
 * 获取指定用户信息API
 * @param userId - 要获取的用户ID
 * @returns Promise - 返回包含用户数据的Promise
 */
export const getUser = (userId: string) => {
    return request.get(`/users/${userId}`).then(response => {
        return response;
    });
}

/**
 * 用户注册API
 * [已修改] 确保注册后的登录状态只存储在当前标签页的sessionStorage中
 * [已修改] 成功获取用户信息后返回Promise，由调用组件处理跳转
 * @param data - 包含用户注册信息的对象
 * @returns Promise - 返回注册结果的Promise
 */
export const userRegister = (data: {
    username: string,
    email: string,
    password: string,
    password_confirm: string,
    profile_picture?: string
}) => {
    // 验证密码和确认密码是否匹配
    if (data.password !== data.password_confirm) {
        return Promise.reject(new Error('密码和确认密码不匹配'));
    }
    
    // 修改为使用/auth/register端点
    return request.post('/auth/register', {
        username: data.username,
        email: data.email,
        password: data.password,
        password_confirm: data.password_confirm, // 添加密码确认字段
        profile_picture: data.profile_picture || undefined
    }, {
        validateStatus: (status) => status >= 200 && status < 300
    }).then(response => {
        // 注册成功后，如果有令牌，保存它
        if (response.data && response.data.access_token) {
            const userStore = useUserStore();
            
            // [已修改] 设置令牌（存储在sessionStorage中）
            userStore.setToken(response.data.access_token, response.data.refresh_token || '');
            
            // [已修改] 获取用户信息，返回Promise以便调用组件处理跳转
            return getCurrentUser().then(() => {
                console.log('[已修改] 注册成功，用户信息获取成功，由组件处理跳转');
                
                // 返回响应以便调用组件处理后续逻辑（如跳转）
                return response;
            }).catch(error => {
                console.error('获取用户信息失败:', error);
                return response;
            });
        }
        return response;
    });
}

/**
 * 用户登出API
 * 注销用户并清除所有本地存储的用户信息
 * @returns Promise - 返回表示操作成功的Promise
 */
export const userLogout = () => {
    const userStore = useUserStore();
    
    // 获取当前令牌用于注销请求
    const token = userStore.getToken();
    
    // 如果没有令牌，直接清除本地用户信息并返回成功
    if (!token) {
        userStore.clearUserInfo();
        return Promise.resolve(true);
    }
    
    return request.post('/auth/logout', {})
        .then(() => {
            // 成功时清除用户信息
            userStore.clearUserInfo();
            return true;
        })
        .catch(() => {
            // 失败时也清除用户信息，确保本地状态干净
            userStore.clearUserInfo();
            return true;
        });
}