<script setup lang="ts">
// [已修改] 导入权限检查工具
import { checkAuth, authClick } from './utils/directives';
import { provide, onMounted } from 'vue';
import { useUserStore } from './utils/state'; // [已修改] 导入用户状态

// [已修改] 提供全局的权限检查方法，让所有组件都能使用
provide('checkAuth', checkAuth);
provide('authClick', authClick);

const userStore = useUserStore(); // [已修改] 获取用户状态

/**
 * [已修改] 添加页面可见性变化监听，确保标签页状态独立
 * 当页面从隐藏变为可见时，重新加载用户数据
 */
onMounted(() => {
  // 页面可见性变化时检查登录状态
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      console.log('[已修改] 标签页变为可见，重新检查登录状态');
      // 重新从sessionStorage加载用户数据
      userStore.localStorageUserData();
    }
  });
  
  // 初始加载用户数据
  userStore.localStorageUserData();
});
</script>

<template>
  <el-container direction="vertical">
    <router-view />
  </el-container>
</template>

<style scoped></style>
