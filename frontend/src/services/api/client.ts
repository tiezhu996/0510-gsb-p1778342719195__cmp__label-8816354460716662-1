/**
 * Axios客户端配置
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosError } from 'axios';
import { API_BASE_URL } from '../../utils/constants';
import { getToken, removeToken, removeUser } from '../../utils/helpers';

// 创建Axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加Token到请求头
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：处理错误
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // 处理401未授权错误
    if (error.response?.status === 401) {
      // 清除本地存储的Token和用户信息
      removeToken();
      removeUser();
      
      // 使用事件来通知AuthContext更新状态，而不是直接跳转
      // 这样可以让React Router处理导航，避免页面刷新
      const event = new CustomEvent('auth:unauthorized');
      window.dispatchEvent(event);
      
      // 如果当前不在登录页，则延迟跳转，让React组件有机会处理状态更新
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        // 使用setTimeout避免在拦截器中直接跳转，让React组件先处理状态更新
        setTimeout(() => {
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }, 100);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

