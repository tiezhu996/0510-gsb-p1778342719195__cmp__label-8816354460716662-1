/**
 * 认证相关API服务
 */
import apiClient from './client';
import { User } from '../../utils/types';

// 注册请求参数
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// 登录请求参数
export interface LoginRequest {
  username: string;
  password: string;
}

// 登录响应
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// 注册响应
export interface RegisterResponse extends User {}

/**
 * 用户注册
 */
export const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
  const response = await apiClient.post<RegisterResponse>('/api/auth/register', data);
  return response.data;
};

/**
 * 用户登录
 */
export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/api/auth/login', data);
  return response.data;
};

/**
 * 用户登出
 */
export const logout = async (): Promise<void> => {
  await apiClient.post('/api/auth/logout');
};

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/api/auth/me');
  return response.data;
};

