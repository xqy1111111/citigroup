<script setup lang="ts">
import { HomeFilled, Document, Avatar, SwitchButton } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import {useUserStore,useCurrentRepoStore} from "../utils/state.ts";
import {ElMessage, ElMessageBox} from "element-plus";
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
const userStore = useUserStore();

const router = useRouter();
const handleSelect = (key: string) => {
  switch (key) {
    case 'home':
      router.push('/dashboard');
      break;
    case 'workspace':
      // 检查是否有当前仓库
      // const currentRepo = JSON.parse(sessionStorage.getItem('currentRepo') || '{}');
        const currentRepo = useCurrentRepoStore();
      if (!currentRepo.id) {
        ElMessage.warning('Please select a repository first');
        return;
      }
      router.push('/workspace');
      break;
    case 'chat':
      router.push('/chat');
      break;
  }
};

const handleLogout = () => {
  ElMessageBox.confirm(
    'Quit ?',
    'Warning',
    {
      confirmButtonText: 'Confirm',
      cancelButtonText: 'Cancel',
      type: 'warning',
    }
  ).then(() => {

    userStore.clearUserInfo();
    console.log(userStore.isLoggedIn)
    router.push('/login');

  });
};

</script>

<template>
  <el-aside class="navi-bar" width="60px">
    <el-menu default-active="home" class="navi-menu"@select="handleSelect">
      <el-menu-item index="home">
        <el-icon><HomeFilled /></el-icon>
      </el-menu-item>
      <el-menu-item index="workspace">
        <el-icon><Document /></el-icon>
      </el-menu-item>
    </el-menu>

    <el-space direction="vertical" size="large" class="user-section">
      <el-button type="primary" text bg :icon="Avatar" circle />
      <el-button type="primary" @click="handleLogout" text bg :icon="SwitchButton" circle />
    </el-space>
  </el-aside>
</template>

<style scoped>

.navi-bar {
  background-color: #2c2c2c;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
}

.navi-menu {
  width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  --el-menu-bg-color: #2c2c2c;
  --el-menu-hover-bg-color: #fff;
  --el-menu-text-color: #808080;
  --el-menu-active-color: #ffffff;
}

.user-section {
  margin-bottom: 20px;
}

</style>