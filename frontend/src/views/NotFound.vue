<script setup lang="ts">
</script>

<template>
  <el-main class="main-frame">
    <el-result icon="error" title="错误" subtitle="您访问的页面不存在">
      <template #extra>
        <router-link to="/">
          <el-button type="primary">返回</el-button>
        </router-link>
      </template>
    </el-result>
  </el-main>
</template>

<style scoped>
.main-frame {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>