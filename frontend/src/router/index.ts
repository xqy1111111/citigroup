import { createRouter, createWebHashHistory } from "vue-router";
import { ElMessage } from 'element-plus';
import { useUserStore } from '../utils/state';
import { getCurrentUser } from '../api/user';

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      redirect: '/home',
    },
    {
      path: '/home',
      redirect: '/login',
      component: () => import('../views/Home.vue'),
      children: [
        {
          path: '/login',
          name: 'Login',
          component: () => import('../views/home/Login.vue'),
          meta: {
            title: 'Login',
            requiresAuth: false
          }
        },
        {
          path: '/register',
          name: 'Register',
          component: () => import('../views/home/Register.vue'),
          meta: {
            title: 'Register',
            requiresAuth: false
          }
        },
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: () => import('../views/home/Dashboard.vue'),
          meta: {
            title: 'Dashboard',
            requiresAuth: true
          }
        }
      ]
    },
    {
      path: '/workspace',
      redirect: '/repo',
      component: () => import('../views/Workspace.vue'),
      children: [
        {
          path: '/repo',
          name: 'Repo',
          component: () => import('../views/workspace/Repository.vue'),
          meta: {
            title: 'Repository',
            requiresAuth: true
          }
        },
        {
          path: '/file',
          name: 'File',
          component: () => import('../views/workspace/File.vue'),
          meta: {
            title: 'File',
            requiresAuth: true
          }
        },
        {
          path: '/chat',
          name: 'Chat',
          component: () => import('../views/workspace/Chat.vue'),
          meta: {
            title: 'Chat',
            requiresAuth: true
          }
        },
      ]
    },
    {
      path: '/404',
      name: '404',
      component: () => import('../views/NotFound.vue'),
      meta: {
        title: '404',
        requiresAuth: false
      }
    },
    {
      path: '/:catchAll(.*)',
      redirect: '/404'
    }
  ]
});

/**
 * 全局前置守卫
 * [已修改] 确保每个标签页独立验证认证状态，不依赖共享存储
 * [已修改] 增强了登录后的路由跳转逻辑
 */
router.beforeEach(async (to, from, next) => {
  // 使用Pinia存储
  const userStore = useUserStore();
  
  // [已修改] 每次路由变化时都强制重新从sessionStorage加载用户数据
  // 这确保了不同标签页之间不会共享认证状态
  userStore.localStorageUserData();
  
  // [已修改] 检查当前标签页的令牌是否存在（从sessionStorage获取）
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const hasToken = !!userStore.getToken();
  
  // 定义未登录用户可访问的白名单路径
  const publicRoutes = ['/login', '/register', '/404'];
  const isPublicRoute = publicRoutes.includes(to.path);
  
  console.log('[已修改] 路由守卫检查当前标签页状态: ', {
    path: to.path,
    requiresAuth,
    hasToken,
    isPublicRoute,
    tabId: Date.now() // 添加时间戳作为标签页的唯一标识，用于调试
  });
  
  // 加强权限控制逻辑
  if (!hasToken) {
    // 用户未登录
    if (isPublicRoute) {
      // 未登录用户访问公开页面，允许
      // 设置页面标题
      if (to.meta.title) {
        document.title = to.meta.title as string;
      }
      next();
    } else {
      // [已修改] 未登录用户访问非公开页面，显示更友好的提示并重定向
      // 将当前路径保存在query参数中，以便登录后可以跳回该页面
      ElMessage.warning('请先登录后再访问此页面');
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      });
    }
  } else {
    // 已登录用户
    if (to.path === '/login' || to.path === '/register') {
      // [已修改] 已登录用户尝试访问登录/注册页，重定向到仪表板
      console.log('[已修改] 已登录用户尝试访问登录/注册页面，重定向到dashboard');
      next('/dashboard');
    } else {
      // 已登录用户访问其他页面，允许
      // 设置页面标题
      if (to.meta.title) {
        document.title = to.meta.title as string;
      }
      next();
    }
  }
});

export { router }