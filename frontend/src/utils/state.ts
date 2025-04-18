import { defineStore } from 'pinia';
import type { file } from '../api/file';
import type { repo, result } from '../api/repo';
import type { userData } from '../api/user';
import type { chat, chatHistory } from '../api/chat';

/**
 * 用户状态管理
 * [已修改] 使用sessionStorage替代localStorage，确保每个标签页状态独立
 */
export const useUserStore = defineStore('user', {
    state: () => ({
        id: '',
        username: '',
        email: '',
        profile_picture: '',
        repos: [] as string[],
        collaborations: [] as string[],
        isLoggedIn: false,
        token: '',
        refreshToken: ''
    }),

    actions: {
        /**
         * 设置用户信息
         * @param info 用户数据
         */
        setUserInfo(info: userData) {
            this.$patch({
                id: info.id,
                username: info.username,
                email: info.email,
                profile_picture: info.profile_picture,
                repos: info.repos,
                collaborations: info.collaborations,
                isLoggedIn: true
            });
            // 使用sessionStorage存储用户数据，提高安全性
            sessionStorage.setItem('user', JSON.stringify(info))
        },

        /**
         * 设置访问令牌
         * [已修改] 使用sessionStorage而非localStorage，确保每个标签页状态独立
         * @param token JWT访问令牌
         * @param refreshToken 可选的刷新令牌
         */
        setToken(token: string, refreshToken?: string) {
            this.token = token;
            
            // [已修改] 如果提供了刷新令牌，也保存它到sessionStorage
            if (refreshToken) {
                this.refreshToken = refreshToken;
                sessionStorage.setItem('refreshToken', refreshToken);
            }
            
            // [已修改] 使用sessionStorage而非localStorage，确保每个标签页状态独立
            sessionStorage.setItem('token', token);
        },

        /**
         * 获取访问令牌
         * [已修改] 从sessionStorage获取令牌，确保标签页状态独立
         * @returns 当前访问令牌
         */
        getToken(): string {
            // [已修改] 如果内存中没有令牌，尝试从sessionStorage读取
            if (!this.token) {
                this.token = sessionStorage.getItem('token') || '';
            }
            return this.token;
        },
        
        /**
         * 获取刷新令牌
         * [已修改] 从sessionStorage获取刷新令牌
         * @returns 当前刷新令牌
         */
        getRefreshToken(): string {
            if (!this.refreshToken) {
                this.refreshToken = sessionStorage.getItem('refreshToken') || '';
            }
            return this.refreshToken;
        },

        /**
         * 清除用户信息
         * [已修改] 确保清除所有sessionStorage中的令牌
         */
        clearUserInfo() {
            this.$patch({
                id: '',
                username: '',
                email: '',
                profile_picture: '',
                repos: [],
                collaborations: [],
                isLoggedIn: false,
                token: '',
                refreshToken: ''
            });
            // [已修改] 清除所有存储，从sessionStorage中移除令牌
            sessionStorage.removeItem('refreshToken');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
        },

        /**
         * 更新用户仓库列表
         * @param repos 新的仓库列表
         */
        updateRepos(repos: string[]) {
            this.$patch({
                repos: repos
            });
            // 更新session存储
            const userData = {
                id: this.id, 
                username: this.username, 
                email: this.email, 
                profile_picture: this.profile_picture, 
                repos: this.repos, 
                collaborations: this.collaborations
            };
            sessionStorage.setItem('user', JSON.stringify(userData));
        },

        /**
         * 从本地存储加载用户数据
         * [已修改] 仅从sessionStorage加载数据，确保标签页状态独立
         */
        localStorageUserData() {
            // [已修改] 尝试从sessionStorage恢复令牌
            const token = sessionStorage.getItem('token');
            if (token) {
                this.token = token;
            }
            
            // [已修改] 尝试从sessionStorage获取刷新令牌
            const refreshToken = sessionStorage.getItem('refreshToken');
            if (refreshToken) {
                this.refreshToken = refreshToken;
            }
            
            // 从sessionStorage获取用户信息
            const userData = JSON.parse(sessionStorage.getItem('user') || '{}');
            if (userData && Object.keys(userData).length > 0) {
                this.setUserInfo(userData);
            }
        }
    },
});


export const useCurrentRepoStore = defineStore('currentRepo', {
    state: () => ({
        id: '',
        name: '',
        desc: '',
        owner_id: '',
        collaborators: [] as string[],
        files: [] as file[],
        results: [] as file[],
    }),

    actions: {
        // 设置当前仓库信息
        setCurrentRepoInfo(repo: repo) {
            this.$patch({
                id: repo.id,
                name: repo.name,
                desc: repo.desc,
                owner_id: repo.owner_id,
                collaborators: repo.collaborators,
                files: repo.files,
                results: repo.results,
            });
            sessionStorage.setItem('currentRepo', JSON.stringify(repo));
        },

        // 清除当前仓库信息
        clearCurrentRepoInfo() {
            this.$patch({
                id: '',
                name: '',
                desc: '',
                owner_id: '',
                collaborators: [],
                files: [],
                results: [],

            });
            sessionStorage.setItem('currentRepo', JSON.stringify({ id: this.id, name: this.name, desc: this.desc, owner_id: this.owner_id, collaborators: this.collaborators, files: this.files, results: this.results }));
        },

        // 更新当前仓库文件列表
        updateCurrentRepoFiles(files: file[]) {
            this.$patch({
                files: files
            });
            sessionStorage.setItem('currentRepo', JSON.stringify({ id: this.id, name: this.name, desc: this.desc, owner_id: this.owner_id, collaborators: this.collaborators, files: this.files, results: this.results }));
        },

        updateCurrentRepoResults(results: result[]) {
            this.results = results;
            sessionStorage.setItem('currentRepo', JSON.stringify({ id: this.id, name: this.name, desc: this.desc, owner_id: this.owner_id, collaborators: this.collaborators, files: this.files, results: this.results }));
        },

        updateCurrentRepoNameAndDesc(name: string, desc: string) {
            this.$patch({
                name: name,
                desc: desc,
            });
            sessionStorage.setItem('currentRepo', JSON.stringify({ id: this.id, name: this.name, desc: this.desc, owner_id: this.owner_id, collaborators: this.collaborators, files: this.files, results: this.results }));
        },

        updateCurrentRepoCollaborators(collaborators: string[]) {
            this.$patch({
                collaborators: collaborators,
            });
            sessionStorage.setItem('currentRepo', JSON.stringify({ id: this.id, name: this.name, desc: this.desc, owner_id: this.owner_id, collaborators: this.collaborators, files: this.files, results: this.results }));
        },

        // 从sessionStorage中获取当前仓库信息
        localStorageCurrentRepoData() {
            const repoData = JSON.parse(sessionStorage.getItem('currentRepo') || '{}');
            if (repoData) {
                this.setCurrentRepoInfo(repoData);
            }
        }
    }
})


interface item {
  key: string,
  value: string,
}


export const useCurrentFileStore = defineStore('currentFile', {
    state: () => ({
        file_id: '',
        filename: '',
        size: 0,
        uploaded_at: '',
        status: '',
        resultData: {
            res_id: '',
            file_id: '',
            content: {
                current_transaction: [] as item[],
                related_transactions: [] as item[],
                operation_information: [] as item[],
                initial_account: [] as item[],
                target_account: [] as item[],
                fraud_detection: [] as item[],
            }
        }
    }),

    actions: {
        // 设置当前文件信息
        setCurrentFileInfo(file: file, resultData: result) {
            this.$patch({
                file_id: file.file_id,
                filename: file.filename,
                size: file.size,
                uploaded_at: file.uploaded_at,
                status: file.status,
                resultData: resultData
            });
            sessionStorage.setItem('currentFile', JSON.stringify({ file_id: this.file_id, filename: this.filename, size: this.size, uploaded_at: this.uploaded_at, status: this.status, resultData: this.resultData }));
        },

        // 清除当前文件信息
        clearCurrentFileInfo() {
            this.$patch({
                file_id: '',
                filename: '',
                size: 0,
                uploaded_at: '',
                status: '',
                resultData: {
                    res_id: '',
                    file_id: '',
                    content: {
                        
                    }
                }
            });
            sessionStorage.setItem('currentFile', JSON.stringify({ file_id: this.file_id, filename: this.filename, size: this.size, uploaded_at: this.uploaded_at, status: this.status, resultData: this.resultData }));
        },

        // 从sessionStorage中获取当前文件信息
        localStorageCurrentFileInfo() {
            const fileData = JSON.parse(sessionStorage.getItem('currentFile') || '{}');
            if (fileData) {
                this.$patch({
                    file_id: fileData.file_id,
                    filename: fileData.filename,
                    size: fileData.size,
                    uploaded_at: fileData.uploaded_at,
                    status: fileData.status,
                    resultData: fileData.resultData,
                });
                sessionStorage.setItem('currentFile', JSON.stringify({ file_id: this.file_id, filename: this.filename, size: this.size, uploaded_at: this.uploaded_at, status: this.status, resultData: this.resultData }));                
            }
        }
    }
})

export const useChatHistoryStore = defineStore('chatHistory', {
    state: () => ({
        user_id: '',
        repo_id: '',
        texts: [] as {
            question: chat,
            answer: chat
        }[],
    }),

    actions: {
        // 设置聊天历史
        setChatHistory(history: chatHistory) {
            this.$patch({
                user_id: history.user_id,
                repo_id: history.repo_id,
                texts: history.texts
            });
            sessionStorage.setItem('chatHistory', JSON.stringify(history));
        },

        // 清除聊天历史 后端没有这个功能的支持，算了

        // 更新聊天历史
        updateChatHistory(history: chatHistory) {
            this.$patch({
                texts: history.texts
            });
            sessionStorage.setItem('chatHistory', JSON.stringify(history));
        },

        // 从sessionStorage中获取聊天历史
        localStorageChatHistory() {
            const historyData = JSON.parse(sessionStorage.getItem('chatHistory') || '{}');
            if (historyData) {
                this.setChatHistory(historyData);
            }
        }

    }
})


/* example usage from chat-gpt

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '../utils/state'

const userStore = useUserStore() //注册一个函数方便使用

onMounted(() => {
  userStore.localStorageUserData() // 页面刷新后首先恢复数据,由于pinia是响应式的,因此后面修改数据也会实时更新,不需要重新调用localStorageUserData()
})

const login = () => {
    userStore.setUserInfo({ id: '123456', username: 'dev', email: 'dev@example.com', profile_picture: "", repos: [], collaborations: [] }) //使用写好的方法,修改数据
}
</script>

<template>
    <div>
        <p>用户 ID: {{ userStore.id }}</p> //可以直接这样用
        <p>用户名字: {{ userStore.name }}</p>
        <button @click="login">登录</button>
    </div>
</template>

*/
