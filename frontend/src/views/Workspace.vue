<script setup lang="ts">
import MenuBar from '../components/MenuBar.vue';
import NaviBar from '../components/NaviBar.vue';
import SideBar from '../components/SideBar.vue';
</script>

<template>
  <MenuBar />
  <el-container>
    <NaviBar />
    <el-container>
      <SideBar />
      <router-view />
    </el-container>
  </el-container>
</template>

<style scoped>
</style>