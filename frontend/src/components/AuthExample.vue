<script setup lang="ts">
// [已修改] 示例组件，展示如何使用权限控制功能
import { inject } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import { authClick } from '../utils/directives';

// 获取注入的权限检查方法
const checkAuth = inject('checkAuth') as () => boolean;
const router = useRouter();

// 使用函数式的权限点击检查
const handleAuthAction = authClick(() => {
  ElMessage.success('操作成功，用户已登录');
}, '/dashboard');

// 直接检查登录状态
const checkLoginStatus = () => {
  if (checkAuth()) {
    ElMessage.success('用户已登录');
  } else {
    ElMessage.warning('用户未登录');
    router.push('/login');
  }
};

// [已修改] 添加自定义函数
const customFunc = () => {
  ElMessage.success('自定义函数执行成功');
};
</script>

<template>
  <div class="auth-example">
    <h2>权限控制示例</h2>
    
    <div class="example-section">
      <h3>1. 使用指令控制点击权限</h3>
      <el-button v-auth-click="'/dashboard'" type="primary">
        访问仪表板（使用指令，未登录将提示）
      </el-button>
      
      <el-button v-auth-click="customFunc" type="success">
        执行操作（未登录将提示）
      </el-button>
    </div>
    
    <div class="example-section">
      <h3>2. 使用函数控制点击权限</h3>
      <el-button @click="handleAuthAction" type="warning">
        功能操作（使用authClick函数）
      </el-button>
    </div>
    
    <div class="example-section">
      <h3>3. 使用条件判断</h3>
      <el-button @click="checkLoginStatus" type="info">
        检查登录状态
      </el-button>
      
      <div v-if="checkAuth()" class="auth-content">
        仅登录用户可见的内容
      </div>
      <div v-else class="unauth-content">
        未登录用户可见的内容，请先 
        <router-link to="/login">登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-example {
  padding: 20px;
  border: 1px solid #eaeaea;
  border-radius: 4px;
}

.example-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.auth-content {
  margin-top: 10px;
  padding: 10px;
  background-color: #ebf8f2;
  border-radius: 4px;
}

.unauth-content {
  margin-top: 10px;
  padding: 10px;
  background-color: #fdf6ec;
  border-radius: 4px;
}
</style> 