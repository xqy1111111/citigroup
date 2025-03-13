import { createApp } from 'vue';
import './style.css';
import App from './App.vue';
import ElementPlus from 'element-plus';
import { router } from './router';
import axios from 'axios';
import { createPinia } from 'pinia';

// 根据环境设置API基础URL
const apiBaseUrl = process.env.NODE_ENV === 'development'
  ? 'http://localhost:8000'
  : 'http://localhost:8000';
  
axios.defaults.baseURL = apiBaseUrl;
axios.defaults.timeout = 30000;

createApp(App).use(ElementPlus).use(router).use(createPinia()).mount('#app');
