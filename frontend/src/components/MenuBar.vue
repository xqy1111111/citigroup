<script setup lang="ts">
import { ArrowLeftBold, ElementPlus } from '@element-plus/icons-vue'
import { useRouter } from "vue-router";

const router = useRouter();
// 添加返回上一页的方法
const goBack = () => {
  router.back();
};
</script>

<template>
  <el-header class="menu-bar" height="30px">
    <el-icon :size="28" color="#42a5f5">
      <ElementPlus />
    </el-icon>
    <div class="title-section">
      <el-button type="primary" text :icon="ArrowLeftBold"  @click="goBack"/>
      <span class="title" style="cursor: pointer ">{{ $route.name }}</span>
    </div>
  </el-header>
</template>

<style scoped>

.menu-bar {
  padding-left: 14px;
  background-color: #ddd;
  display: flex;
  align-items: center;
  gap: 20px;
}

.logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.title-section {
  width: 100%;
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: start;
}

.title {
  font-size: medium;
  font-weight: bold;
  text-align: center;
}

</style>