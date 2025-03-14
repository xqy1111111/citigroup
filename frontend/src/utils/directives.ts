import type { ObjectDirective } from 'vue'
import { useUserStore } from './state'
import { ElMessage } from 'element-plus'
import { router } from '../router'

/**
 * [已修改] 点击权限控制指令
 * 用于拦截未登录用户点击需要登录权限的元素
 * 使用方法：v-auth-click="'/dashboard'"
 * 参数可以是：
 * 1. 字符串路径，表示点击后要导航到的路径
 * 2. 函数，会在验证通过后执行
 */
export const vAuthClick: ObjectDirective = {
  mounted(el, binding) {
    el.addEventListener('click', (e: MouseEvent) => {
      const userStore = useUserStore()
      const hasToken = !!userStore.getToken()
      
      // 如果用户未登录
      if (!hasToken) {
        e.preventDefault()
        e.stopPropagation()
        
        // 显示未登录提示
        ElMessage.warning('请先登录后再进行此操作')
        
        // 记录原目标路径
        const targetPath = typeof binding.value === 'string' ? binding.value : '/login'
        const currentPath = router.currentRoute.value.fullPath
        
        // 导航到登录页面并记录重定向地址
        if (currentPath !== '/login' && currentPath !== '/register') {
          router.push({
            path: '/login',
            query: { redirect: targetPath !== '/login' ? targetPath : '/dashboard' }
          })
        }
        
        return false
      } else if (typeof binding.value === 'function') {
        // 如果用户已登录且绑定值是函数，执行该函数
        binding.value(e)
      } else if (typeof binding.value === 'string') {
        // 如果用户已登录且绑定值是字符串路径，导航到该路径
        router.push(binding.value)
      }
    })
  }
}

/**
 * [已修改] 全局权限检查工具函数
 * 用于代码中检查用户是否已登录
 * @returns 用户是否已登录
 */
export const checkAuth = () => {
  const userStore = useUserStore()
  return !!userStore.getToken()
}

/**
 * [已修改] 全局权限点击处理函数
 * 用于非指令方式处理点击权限
 * @param callback 验证通过后的回调函数
 * @param targetPath 目标路径
 * @returns 处理函数
 */
export const authClick = (callback: Function, targetPath: string = '/dashboard') => {
  return (e: MouseEvent) => {
    const userStore = useUserStore()
    const hasToken = !!userStore.getToken()
    
    if (!hasToken) {
      e.preventDefault()
      e.stopPropagation()
      
      // 显示未登录提示
      ElMessage.warning('请先登录后再进行此操作')
      
      // 导航到登录页面并记录重定向地址
      const currentPath = router.currentRoute.value.fullPath
      if (currentPath !== '/login' && currentPath !== '/register') {
        router.push({
          path: '/login',
          query: { redirect: targetPath }
        })
      }
      
      return false
    } else {
      // 用户已登录，执行回调
      return callback(e)
    }
  }
} 