import { createRouter, createWebHashHistory } from "vue-router";
import { ElMessage } from 'element-plus';
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
            requiresAuth: true
          }
        },
        {
          path: '/file',
          name: 'File',
          component: () => import('../views/workspace/File.vue'),
          meta: {
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

router.beforeEach((to, _, next) => {
  const userData = sessionStorage.getItem('user');
  console.log(userData)
  const isLoggedIn = userData ? JSON.parse(userData).id !== '' : false;
  if (!isLoggedIn && to.path !== '/login' && to.path !== '/register') {
    ElMessage.error('Please login first');
    next('/login');
    return;
  }
  // 设置页面标题
  if (to.meta.title) {
    document.title = to.meta.title as string;
  }
  next();
});

export { router }