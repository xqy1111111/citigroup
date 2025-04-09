<script setup lang="ts">
import { computed, ref } from 'vue';
import { userRegister } from '../../api/user';
import { router } from '../../router';
import 'element-plus/theme-chalk/el-message.css'
import { ElMessage } from 'element-plus';

/**
 * 注册表单数据
 */
const username = ref('');  // 用户名
const email = ref('');     // 电子邮件
const password = ref('');  // 密码
const confirmPassword = ref(''); // 确认密码
const avatarUrl = ref(''); // 头像URL，可选

/**
 * 表单字段错误信息
 */
const usernameError = ref('');
const emailError = ref('');
const passwordError = ref('');
const confirmPasswordError = ref('');

/**
 * 注册处理状态
 */
const loading = ref(false);

/**
 * 检查邮箱是否为空
 */
const isEmailEmpty = computed(() => {
  return !email.value;
});

/**
 * 验证邮箱格式是否正确
 */
const isEmailValid = computed(() => {
  if (isEmailEmpty.value) {
    emailError.value = '邮箱不能为空';
    return false;
  }
  
  if (!/^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/.test(email.value)) {
    emailError.value = '请输入有效的电子邮件地址';
    return false;
  }
  
  emailError.value = '';
  return true;
});

/**
 * 验证用户名是否符合规则
 * 规则：3-50个字符，只能包含字母、数字和下划线
 */
const isUsernameValid = computed(() => {
  if (!username.value) {
    usernameError.value = '用户名不能为空';
    return false;
  }
  
  if (username.value.length < 3) {
    usernameError.value = '用户名长度至少为3个字符';
    return false;
  }
  
  if (username.value.length > 50) {
    usernameError.value = '用户名长度不能超过50个字符';
    return false;
  }
  
  if (!/^[a-zA-Z0-9_]+$/.test(username.value)) {
    usernameError.value = '用户名只能包含字母、数字和下划线';
    return false;
  }
  
  usernameError.value = '';
  return true;
});

/**
 * 验证密码强度是否符合要求
 * 规则：至少8个字符，包含至少一个字母和一个数字
 */
const isPasswordValid = computed(() => {
  if (!password.value) {
    passwordError.value = '密码不能为空';
    return false;
  }
  
  if (password.value.length < 8) {
    passwordError.value = '密码长度至少为8个字符';
    return false;
  }
  
  if (!/[A-Za-z]/.test(password.value) || !/[0-9]/.test(password.value)) {
    passwordError.value = '密码必须包含至少一个字母和一个数字';
    return false;
  }
  
  passwordError.value = '';
  return true;
});

/**
 * 验证两次输入的密码是否一致
 */
const isConfirmPasswordValid = computed(() => {
  if (!confirmPassword.value) {
    confirmPasswordError.value = '请确认密码';
    return false;
  }
  
  if (password.value !== confirmPassword.value) {
    confirmPasswordError.value = '两次输入的密码不一致';
    return false;
  }
  
  confirmPasswordError.value = '';
  return true;
});

/**
 * 判断注册按钮是否可用
 * 所有必填字段必须有效
 */
const registerAvailable = computed(() => {
  return isUsernameValid.value && 
         !isEmailEmpty.value && 
         isEmailValid.value && 
         isPasswordValid.value && 
         isConfirmPasswordValid.value;
});

/**
 * 处理用户名输入框失去焦点事件
 */
function handleUsernameBlur() {
  isUsernameValid.value;
}

/**
 * 处理邮箱输入框失去焦点事件
 */
function handleEmailBlur() {
  isEmailValid.value;
}

/**
 * 处理密码输入框失去焦点事件
 */
function handlePasswordBlur() {
  isPasswordValid.value;
}

/**
 * 处理确认密码输入框失去焦点事件
 */
function handleConfirmPasswordBlur() {
  isConfirmPasswordValid.value;
}

/**
 * 执行注册操作
 * 向后端发送用户注册请求并处理响应
 */
function register() {
  // 设置加载状态
  loading.value = true;
  
  // 提交注册表单到后端
  userRegister({
    username: username.value,
    email: email.value,
    password: password.value,
    password_confirm: confirmPassword.value,
    profile_picture: avatarUrl.value || undefined, // 如果为空则不传递
  }).then(response => {
    loading.value = false;
    if (response.status === 200 || response.status === 201) {
      ElMessage.success('注册成功，请登录');
      // 注册成功后跳转到登录页面
      router.push('/login');
    }
  }).catch((error) => {
    // 重置加载状态
    loading.value = false;
    
    // 提取错误信息
    const errorMessage = error.response?.data?.detail || '注册失败';
    const errorCode = error.response?.data?.code || '';
    
    // 根据错误代码或消息处理不同的错误情况
    switch (errorCode) {
      case 'EMAIL_ALREADY_REGISTERED':
        emailError.value = '该邮箱已被注册';
        ElMessage.error('该邮箱已被注册');
        break;
      case 'USERNAME_EXISTS':
        usernameError.value = '该用户名已被使用';
        ElMessage.error('该用户名已被使用');
        break;
      case 'PASSWORD_TOO_WEAK':
        passwordError.value = '密码强度不足';
        ElMessage.error('密码强度不足');
        break;
      case 'PASSWORDS_DO_NOT_MATCH':
        confirmPasswordError.value = '两次输入的密码不一致';
        ElMessage.error('两次输入的密码不一致');
        break;
      default:
        // 分析错误消息文本，兼容旧版API
        if (errorMessage.includes('Email already registered')) {
          emailError.value = '该邮箱已被注册';
          ElMessage.error('该邮箱已被注册');
        } 
        else if (errorMessage.includes('Username already exists')) {
          usernameError.value = '该用户名已被使用';
          ElMessage.error('该用户名已被使用');
        }
        else if (errorMessage.includes('password')) {
          passwordError.value = errorMessage;
          ElMessage.error(errorMessage);
        }
        else {
          ElMessage.error(errorMessage);
        }
    }
  });
}
</script>

<template>
  <el-main class="main-frame">
    <el-card class="register-card">
      <template #header>
        <span class="register-title">注册</span>
      </template>

      <el-form
        label-position="left"
        label-width="auto"
      >
        <el-form-item 
          label="用户名" 
          required
          :error="usernameError"
        >
          <el-input 
            v-model="username" 
            @blur="handleUsernameBlur"
            placeholder="3-50个字符，只能包含字母、数字和下划线"
          />
        </el-form-item>

        <el-form-item 
          label="邮箱" 
          required
          :error="emailError"
        >
          <el-input 
            v-model="email" 
            @blur="handleEmailBlur"
            placeholder="请输入有效的电子邮件地址"
          />
        </el-form-item>

        <el-form-item label="头像链接">
          <el-input 
            v-model="avatarUrl" 
            placeholder="可选，留空将使用默认头像"
          />
        </el-form-item>

        <el-form-item 
          label="密码" 
          required
          :error="passwordError"
        >
          <el-input 
            v-model="password" 
            show-password 
            @blur="handlePasswordBlur"
            placeholder="至少8个字符，包含字母和数字"
          />
        </el-form-item>

        <el-form-item 
          label="确认密码" 
          required
          :error="confirmPasswordError"
        >
          <el-input 
            v-model="confirmPassword" 
            show-password 
            @blur="handleConfirmPasswordBlur"
            placeholder="请再次输入密码"
            @keyup.enter="registerAvailable && register()"
          />
        </el-form-item>

        <div class="button-group">
          <router-link to="/login" v-slot="{ navigate }" class="login-link">
            <span @click="navigate">已有账号？去登录</span>
          </router-link>
          <el-button 
            type="primary" 
            :disabled="!registerAvailable || loading" 
            @click.prevent="register"
            :loading="loading"
          >
            {{ loading ? '注册中...' : '注册' }}
          </el-button>
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-width: 450px;
}

.register-title {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.button-group {
  padding-top: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.login-link {
  color: #409EFF;
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
}

.login-link:hover {
  text-decoration: underline;
}
</style>