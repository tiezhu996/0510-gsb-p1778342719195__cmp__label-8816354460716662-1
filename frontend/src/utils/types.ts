/**
 * TypeScript类型定义
 */

// 用户类型
export interface User {
  id: number;
  username: string;
  email: string;
  role?: string;
  avatar_url?: string | null;
  created_at?: string;
  updated_at?: string;
  is_active?: boolean;
}

// API响应类型
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

