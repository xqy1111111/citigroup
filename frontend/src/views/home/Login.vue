<script setup lang="ts">
import { computed, ref } from 'vue';
import { router } from '../../router';
import { useUserStore } from '../../utils/state';
import { userLogin, getUser } from '../../api/user';
import { ElMessage } from 'element-plus';
import 'element-plus/theme-chalk/el-message.css'

const userStore = useUserStore();

const email = ref('');
const password = ref('');

const isEmailEmpty = computed(() => {
  return !email.value;
});

const isEmailValid = computed(() => {
  return /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/.test(email.value);
});

const loginAvailable = computed(() => {
  return !isEmailEmpty.value && isEmailValid.value && password.value;
});

function login() {
  userLogin({
    username: '',
    email: email.value,
    password: password.value,
    profile_picture: '',
  }).then(response => {
    if (response.status == 200) {
      getUser(response.data.user_id).then(response => {
        userStore.setUserInfo(response.data);
        router.push({ path: '/dashboard' }).then(() => {
          router.go(0);
        });

      });
    } 
  }).catch(() => {
    ElMessage.error(`Wrong email or password`);
    email.value = '';
    password.value = '';
  });
}

</script>

<template>
  <el-main class="main-frame">
    <el-card class="login-card">
      <template #header>
        <span class="login-title">Login</span>
      </template>
      <el-form
        label-position="left"
        label-width="auto"
      >
        <el-form-item label="Email">
          <el-input v-model="email" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="password" show-password />
        </el-form-item>
        <div class="button-group">
          <router-link to="/register" v-slot="{navigate}">
            <el-button @click="navigate">Register</el-button>
          </router-link>
          <el-button :disabled="!loginAvailable" type="primary" @click.prevent="login">Login</el-button>
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

.login-card {
  width: 40%;
  padding: 10px;
}

.login-title {
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