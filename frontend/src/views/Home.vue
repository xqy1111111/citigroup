<script setup lang="ts">
import MenuBar from '../components/MenuBar.vue';
import NaviBar from '../components/NaviBar.vue';
</script>

<template>
  <MenuBar />
  <el-container>
    <NaviBar />
    <router-view />
  </el-container>
</template>

<style scoped>
</style>