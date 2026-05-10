/**
 * 登录页面
 */
import React, { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(formData.username, formData.password);
      navigate('/chat');
    } catch (err: any) {
      setError(err.message || '登录失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-100">
      <div className="mx-auto flex min-h-screen max-w-md items-center px-4 py-10">
        <div className="w-full rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-sm p-8 shadow-elevated transition-smooth">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 shadow-lg">
              <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">欢迎回来</h1>
            <p className="mt-2 text-sm text-slate-600">登录您的账户以继续</p>
          </div>

          {error && (
            <div className="mb-6 rounded-xl border border-red-200/80 bg-gradient-to-r from-red-50 to-red-50/50 px-4 py-3 text-sm text-red-700 shadow-soft">
              <div className="flex items-center gap-2">
                <svg className="h-5 w-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{error}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="mb-2 block text-sm font-semibold text-slate-700">
                用户名或邮箱
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                autoComplete="username"
                placeholder="请输入用户名或邮箱"
                className="mt-1 w-full rounded-xl border border-slate-300/80 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 shadow-soft transition-smooth focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:shadow-md"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-2 block text-sm font-semibold text-slate-700">
                密码
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                autoComplete="current-password"
                placeholder="请输入密码"
                className="mt-1 w-full rounded-xl border border-slate-300/80 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 shadow-soft transition-smooth focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:shadow-md"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="gradient-primary hover:gradient-primary-hover inline-flex w-full items-center justify-center rounded-xl px-4 py-3.5 text-sm font-semibold text-white shadow-lg transition-smooth hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:shadow-lg"
            >
              {isLoading ? (
                <>
                  <svg className="mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  登录中...
                </>
              ) : (
                '登录'
              )}
            </button>
          </form>

          <div className="mt-8 text-center text-sm text-slate-600">
            还没有账号？{' '}
            <Link to="/register" className="font-semibold text-blue-600 transition-colors hover:text-blue-700">
              立即注册
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

