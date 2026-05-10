/**
 * 应用常量定义
 */

// API基础URL
// 开发环境强制使用相对路径通过Vite代理，生产环境使用完整URL
// 强制开发模式使用空字符串，忽略.env文件中的VITE_API_BASE_URL（避免CORS问题）
const isDev = import.meta.env.DEV || import.meta.env.MODE === 'development';
// 开发模式强制使用空字符串以通过Vite代理，生产模式使用环境变量或默认值
export const API_BASE_URL = isDev ? '' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');

// 调试日志
console.log('[API配置] 开发模式:', isDev);
console.log('[API配置] MODE:', import.meta.env.MODE);
console.log('[API配置] DEV:', import.meta.env.DEV);
console.log('[API配置] PROD:', import.meta.env.PROD);
console.log('[API配置] VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
console.log('[API配置] 最终 API_BASE_URL:', API_BASE_URL);

// WebSocket URL
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// Token存储键名
export const TOKEN_KEY = 'auth_token';

// 用户信息存储键名
export const USER_KEY = 'user_info';

