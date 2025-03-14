<script setup lang="ts">
import { Files, Folder, Document, DocumentChecked, Collection } from '@element-plus/icons-vue';
import { useCurrentRepoStore, useCurrentFileStore,useUserStore } from '../utils/state';
import { onMounted, computed } from 'vue';
import {getRepo} from "../api/repo.ts";
import {router} from "../router";
import { ElMessage } from 'element-plus';
import { checkAuth } from '../utils/directives';

const currentRepoStore = useCurrentRepoStore();
const currentFileStore = useCurrentFileStore();
const userStore = useUserStore();

onMounted(() => {
  currentRepoStore.localStorageCurrentRepoData();
  currentFileStore.localStorageCurrentFileInfo();
});

const handleFileSelect = (fileId: string) => {
  if (!checkAuth()) {
    ElMessage.warning('请先登录后再访问此页面');
    router.push({
      path: '/login',
      query: { redirect: router.currentRoute.value.fullPath }
    });
    return;
  }
  
  const selectedFile = currentRepoStore.files.find(file => file.file_id === fileId);
  if (selectedFile) {
    currentFileStore.setCurrentFileInfo(selectedFile);
  }
};

const otherRepos = computed(() => {
  return userStore.repos.filter(repoId => repoId !== currentRepoStore.id);
});

const naviToRepo = (id: string) => {
  if (!checkAuth()) {
    ElMessage.warning('请先登录后再访问此页面');
    router.push({
      path: '/login',
      query: { redirect: '/repo' }
    });
    return;
  }
  
  getRepo(id).then(response => {
    if (response.status === 200) {
      console.log(response);
      currentRepoStore.setCurrentRepoInfo(response.data);
      router.push('/repo');
    }
  }).catch(error => {
    console.log(error);
  });
};

</script>

<template>
  <el-aside class="side-bar" width="200px">
    <el-menu :default-active="currentFileStore.file_id" class="side-menu">
      <el-sub-menu index="original" class="side-sub-menu">
        <template #title>
          <el-icon><Files /></el-icon>
          <span>File</span>
        </template>
        <template v-if="currentRepoStore.id">
          <el-menu-item
              v-for="file in currentRepoStore.files"
              :key="file.file_id"
              :index="file.file_id"
              @click="handleFileSelect(file.file_id)"
          >
            <el-icon v-if="file.status === 'uploaded'"><Document /></el-icon>
            <el-icon v-else><DocumentChecked /></el-icon>
            {{ file.filename }}
          </el-menu-item>
        </template>
      </el-sub-menu>

      <el-sub-menu index="history">
        <template #title>
          <el-icon><Collection /></el-icon>
          <span>History</span>
        </template>
        <el-menu-item
            v-for="repoId in otherRepos"
            :key="repoId"
            :index="repoId"
            @click="naviToRepo(repoId)"
        >
          <el-icon><Folder /></el-icon>
          {{ repoId}}
        </el-menu-item>
      </el-sub-menu>
    </el-menu>
  </el-aside>
</template>

<style scoped>

.side-bar {
  background-color: #f3f3f3;
  display: flex;
  flex-direction: column;
}

.side-menu {
  width: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  --el-menu-bg-color: #f3f3f3;
  --el-menu-hover-bg-color: #e4e6f1;
  --el-menu-text-color: #2c2c2c;
  --el-menu-active-color: #409eff;
  --el-menu-item-height: 25px;
}

</style>