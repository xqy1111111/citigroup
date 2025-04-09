<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { router } from '../../router';
import { useUserStore } from '../../utils/state';
import { userLogin, getCurrentUser } from '../../api/user';
import { ElMessage } from 'element-plus';
import { useRoute } from 'vue-router';
import 'element-plus/theme-chalk/el-message.css'

// 全局状态
const userStore = useUserStore();
const route = useRoute();

// 表单数据
const identifier = ref(''); // 可以是用户名或邮箱
const password = ref('');

// 错误状态
const identifierError = ref('');
const passwordError = ref('');
const loginError = ref('');

// 加载状态
const loading = ref(false);

/**
 * 检查用户标识符是否为空
 */
const isIdentifierEmpty = computed(() => {
  return !identifier.value;
});

/**
 * 验证用户标识符(用户名或邮箱)是否有效
 */
const isIdentifierValid = computed(() => {
  if (isIdentifierEmpty.value) {
    identifierError.value = '用户名或邮箱不能为空';
    return false;
  }
  
  // 验证为邮箱格式或用户名格式
  const isEmail = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/.test(identifier.value);
  const isUsername = /^[a-zA-Z0-9_]{3,50}$/.test(identifier.value);
  
  if (!isEmail && !isUsername) {
    identifierError.value = '请输入有效的用户名或电子邮件地址';
    return false;
  }
  
  identifierError.value = '';
  return true;
});

/**
 * 验证密码是否符合要求
 */
const isPasswordValid = computed(() => {
  if (!password.value) {
    passwordError.value = '密码不能为空';
    return false;
  }
  
  if (password.value.length < 6) {
    passwordError.value = '密码长度至少为6个字符';
    return false;
  }
  
  passwordError.value = '';
  return true;
});

/**
 * 计算登录按钮是否可用
 */
const loginAvailable = computed(() => {
  return isIdentifierValid.value && isPasswordValid.value;
});

/**
 * 在标识符输入框失去焦点时验证
 */
function handleIdentifierBlur() {
  isIdentifierValid.value;
}

/**
 * 在密码输入框失去焦点时验证
 */
function handlePasswordBlur() {
  isPasswordValid.value;
}

/**
 * 执行登录操作
 * 发送凭据到后端，处理响应或错误
 */
function login() {
  // 清除先前的错误信息
  loginError.value = '';
  
  // 设置加载状态
  loading.value = true;
  
  // 判断标识符是邮箱还是用户名
  const isEmail = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/.test(identifier.value);
  
  // 调用登录API
  userLogin({
    username: isEmail ? '' : identifier.value,
    email: isEmail ? identifier.value : '',
    password: password.value,
    profile_picture: '',
  }).then(response => {
    if (response.data.access_token) {
      // 登录成功后，先获取用户信息再跳转
      getCurrentUser().then(userResponse => {
        // 完成登录和用户信息获取
        loading.value = false;
        ElMessage.success('登录成功');
        
        // 检查是否有重定向URL
        const redirectPath = route.query.redirect as string || '/dashboard';
        console.log('[已修改] 登录成功，准备跳转到:', redirectPath);
        
        // 确保在下一个事件循环中执行跳转，给Vue足够时间更新状态
        setTimeout(() => {
          router.push(redirectPath);
        }, 10);
      }).catch(error => {
        // 获取用户信息失败，但登录成功，仍然跳转
        console.error('[已修改] 获取用户信息失败，但仍然允许跳转', error);
        loading.value = false;
        ElMessage.success('登录成功');
        
        const redirectPath = route.query.redirect as string || '/dashboard';
        router.push(redirectPath);
      });
    } else {
      // 响应格式错误
      loading.value = false;
      loginError.value = '登录响应格式错误';
      ElMessage.error('登录响应格式错误');
    }
  }).catch((error) => {
    loading.value = false;
    
    // 提取错误信息
    const errorMessage = error.response?.data?.detail || '登录失败';
    const errorCode = error.response?.data?.code || '';
    
    // 根据错误代码或消息内容提供友好的错误提示
    switch (errorCode) {
      case 'INVALID_CREDENTIALS':
        loginError.value = '用户名或密码错误';
        ElMessage.error('用户名或密码错误');
        break;
      case 'USER_NOT_FOUND':
        loginError.value = '用户不存在';
        ElMessage.error('用户不存在');
        break;
      case 'ACCOUNT_LOCKED':
        loginError.value = '账户已锁定，请联系管理员';
        ElMessage.error('账户已锁定，请联系管理员');
        break;
      default:
        // 分析错误消息内容
        if (errorMessage.includes('Invalid credentials') || 
            errorMessage.includes('No user found') ||
            errorMessage.includes('Incorrect password')) {
          loginError.value = '用户名或密码错误';
          ElMessage.error('用户名或密码错误');
        }
        else if (errorMessage.includes('Account is locked')) {
          loginError.value = '账户已锁定，请联系管理员';
          ElMessage.error('账户已锁定，请联系管理员');
        }
        else {
          loginError.value = errorMessage;
          ElMessage.error(errorMessage);
        }
    }
  });
}

/**
 * 组件挂载时检查用户是否已登录
 */
onMounted(() => {
  // 如果用户已登录，重定向到仪表板或请求的URL
  if (userStore.isLoggedIn && userStore.getToken()) {
    const redirectPath = route.query.redirect as string || '/dashboard';
    router.push(redirectPath);
  }
});
</script>

<template>
  <el-main class="main-frame">
    <el-card class="login-card">
      <template #header>
        <span class="login-title">登录</span>
      </template>
      <el-form
        label-position="left"
        label-width="auto"
      >
        <el-form-item 
          label="用户名/邮箱" 
          :error="identifierError"
        >
          <el-input 
            v-model="identifier" 
            @blur="handleIdentifierBlur"
            placeholder="请输入您的用户名或邮箱"
          />
        </el-form-item>
        
        <el-form-item 
          label="密码"
          :error="passwordError"
        >
          <el-input 
            v-model="password" 
            show-password
            @blur="handlePasswordBlur"
            placeholder="请输入您的密码"
            @keyup.enter="loginAvailable && login()"
          />
        </el-form-item>
        
        <div v-if="loginError" class="error-message">
          {{ loginError }}
        </div>
        
        <div class="button-group">
          <router-link to="/register" v-slot="{navigate}" class="register-link">
            <span @click="navigate">没有账号？去注册</span>
          </router-link>
          <el-button 
            :disabled="!loginAvailable || loading" 
            type="primary" 
            @click.prevent="login"
            :loading="loading"
          >
            {{ loading ? '登录中...' : '登录' }}
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

.login-card {
  width: 40%;
  padding: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-width: 450px;
}

.login-title {
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

.error-message {
  color: #f56c6c;
  font-size: 14px;
  margin-bottom: 15px;
  text-align: center;
}

.register-link {
  color: #409EFF;
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
}

.register-link:hover {
  text-decoration: underline;
}
</style>