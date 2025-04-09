<script setup lang="ts">
import MenuBar from '../components/MenuBar.vue';
import NaviBar from '../components/NaviBar.vue';
import { useRoute, onBeforeRouteUpdate } from 'vue-router';
import { onMounted, ref, watch } from 'vue';

const route = useRoute();
const currentPath = ref(route.path);

onMounted(() => {
  console.log('[已修改] Home组件已加载，当前路径:', route.path);
  currentPath.value = route.path;
});

watch(
  () => route.path,
  (newPath) => {
    console.log('[已修改] 路由已更新，新路径:', newPath);
    currentPath.value = newPath;
  }
);

onBeforeRouteUpdate((to, from) => {
  console.log(`[已修改] 路由将从 ${from.path} 更新到 ${to.path}`);
});
</script>

<template>
  <MenuBar />
  <el-container>
    <NaviBar />
    <router-view :key="currentPath" />
  </el-container>
</template>

<style scoped>
.el-container {
  min-height: calc(100vh - 60px);
}
</style>