/**
 * 路由配置
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatHomePage from './pages/ChatHomePage';
import ChatRoomPage from './pages/ChatRoomPage';
import PrivateChatPage from './pages/PrivateChatPage';
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/ProtectedRoute';

const Router: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* 公开路由 */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* 聊天路由 */}
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <Layout>
                <ChatHomePage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat/room/:room_id"
          element={
            <ProtectedRoute>
              <Layout>
                <ChatRoomPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat/private/:user_id"
          element={
            <ProtectedRoute>
              <Layout>
                <PrivateChatPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* 默认重定向 */}
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default Router;

