<script setup lang="ts">
import { computed, ref } from 'vue';
import { userRegister } from '../../api/user';
import { router } from '../../router';
import 'element-plus/theme-chalk/el-message.css'
import { ElMessage } from 'element-plus';

const username = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const avatarUrl = ref('');

const isEmailEmpty = computed(() => {
  return !email.value;
});

const isEmailValid = computed(() => {
  return /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/.test(email.value);
});

const registerAvailable = computed(() => {
  return !isEmailEmpty.value && isEmailValid.value && password.value && confirmPassword.value && password.value === confirmPassword.value;
});

function register() {
  userRegister({
    username: username.value,
    email: email.value,
    password: password.value,
    profile_picture: avatarUrl.value || 'default',
  }).then(response => {
    if (response.status === 200) {
      router.push('/login').then(() => {
        router.go(0);  // 强制刷新当前页面
      });
    }
  }).catch(() => {
    ElMessage.error('Register failed');
  });
}
</script>

<template>
  <el-main class="main-frame">
    <el-card class="register-card">
      <template #header>
        <span class="register-title">Register</span>
      </template>

      <el-form
        label-position="left"
        label-width="auto"
      >

        <el-form-item label="Username" required>
          <el-input v-model="username" />
        </el-form-item>

        <el-form-item label="Email" required>
          <el-input v-model="email" />
        </el-form-item>

        <el-form-item label="Avatar link" required>
          <el-input v-model="avatarUrl" />
        </el-form-item>

        <el-form-item label="Password" required>
          <el-input v-model="password" show-password />
        </el-form-item>

        <el-form-item label="Confirm Password" required>
          <el-input v-model="confirmPassword" show-password />
        </el-form-item>

        <div class="button-group">
          <router-link to="/login" v-slot="{ navigate }">
            <el-button @click="navigate">Back to Login</el-button>
          </router-link>
          <el-button type="primary" :disabled="!registerAvailable" @click.prevent="register">Register</el-button>
        </div>

      </el-form>
    </el-card>
  </el-main>
</template>

<style scoped>
.main-frame {
  width: 100%;
  height: calc(100vh - 30px);
  display: flex;
  justify-content: center;
  align-items: center;
}

.register-card {
  width: 40%;
  padding: 10px;
}

.register-title {
  font-size: 20px;
  font-weight: bold;
}

.button-group {
  padding-top: 10px;
  display: flex;
  gap: 30px;
  align-items: center;
  justify-content: space-between;
}
</style>