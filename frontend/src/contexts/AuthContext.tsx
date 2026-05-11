/**
 * 认证上下文
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../utils/types';
import { getToken, setToken, removeToken, getUser, setUser, removeUser } from '../utils/helpers';
import * as authService from '../services/api/authService';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUserState] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // 初始化：检查是否有已保存的用户信息
  useEffect(() => {
    const initAuth = async () => {
      const token = getToken();
      const savedUser = getUser();

      if (token && savedUser) {
        // 先使用保存的用户信息，确保用户可以立即看到页面
        setUserState(savedUser);
        
        // 然后在后台验证Token是否有效
        try {
          const currentUser = await authService.getCurrentUser();
          // 验证成功，更新用户信息
          setUserState(currentUser);
          setUser(currentUser);
        } catch (error: any) {
          // 只有在明确是401错误时才清除用户信息（token无效）
          // 如果是网络错误或其他错误，保留用户信息，让用户继续使用
          if (error.response?.status === 401) {
            // Token无效，清除本地存储
            removeToken();
            removeUser();
            setUserState(null);
          }
          // 其他错误（如网络错误）不影响，继续使用保存的用户信息
        }
      } else {
        // 没有token或用户信息，确保状态为空
        setUserState(null);
      }
      setIsLoading(false);
    };

    initAuth();

    // 监听未授权事件，当API返回401时清除用户状态
    const handleUnauthorized = () => {
      removeToken();
      removeUser();
      setUserState(null);
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);

    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, []);

  // 登录
  const login = async (username: string, password: string): Promise<void> => {
    try {
      const response = await authService.login({ username, password });
      setToken(response.access_token);
      setUser(response.user);
      setUserState(response.user);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '登录失败，请检查用户名和密码';
      throw new Error(errorMessage);
    }
  };

  // 注册
  const register = async (username: string, email: string, password: string): Promise<void> => {
    try {
      await authService.register({ username, email, password });
      // 注册成功后自动登录
      await login(username, password);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '注册失败，请检查输入信息';
      throw new Error(errorMessage);
    }
  };

  // 登出
  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } catch (error) {
      // 即使API调用失败，也清除本地存储
      console.error('登出API调用失败:', error);
    } finally {
      removeToken();
      removeUser();
      setUserState(null);
    }
  };

  // 刷新用户信息
  const refreshUser = async (): Promise<void> => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUserState(currentUser);
      setUser(currentUser);
    } catch (error) {
      // 获取用户信息失败，清除本地存储
      removeToken();
      removeUser();
      setUserState(null);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

