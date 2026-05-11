/**
 * 工具函数
 */

import { TOKEN_KEY, USER_KEY } from './constants';
import { User } from './types';

/**
 * 存储Token
 */
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * 获取Token
 */
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * 移除Token
 */
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * 存储用户信息
 */
export const setUser = (user: User): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/**
 * 获取用户信息
 */
export const getUser = (): User | null => {
  const userStr = localStorage.getItem(USER_KEY);
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  }
  return null;
};

/**
 * 移除用户信息
 */
export const removeUser = (): void => {
  localStorage.removeItem(USER_KEY);
};

/**
 * 格式化日期
 */
export const formatDate = (date: string | Date): string => {
  const d = new Date(date);
  return d.toLocaleString('zh-CN');
};

