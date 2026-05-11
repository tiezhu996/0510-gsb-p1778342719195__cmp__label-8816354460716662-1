/**
 * 群聊页面
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import {
  getChatRoom,
  getChatRoomMessages,
  joinChatRoom,
  inviteUserToRoom,
  ChatRoom,
  ChatMessage
} from '../services/api/chatService';
import ChatMessageList from '../components/Chat/ChatMessageList';
import ChatInput from '../components/Chat/ChatInput';

import Modal from '../components/ui/Modal';
import Toast, { ToastType } from '../components/ui/Toast';

const ChatRoomPage: React.FC = () => {
  const { room_id } = useParams<{ room_id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isConnected, sendChatMessage, joinRoom, leaveRoom, onMessage } = useWebSocket();

  const [room, setRoom] = useState<ChatRoom | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(true);

  // Invite Modal State
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [inviteUsername, setInviteUsername] = useState('');
  const [inviting, setInviting] = useState(false);

  // Toast State
  const [toast, setToast] = useState<{ message: string, type: ToastType } | null>(null);

  const pageSize = 50;

  useEffect(() => {
    if (room_id) {
      loadRoom();
      loadMessages(1);
    }

    return () => {
      // 离开页面时离开房间
      if (room_id && isConnected) {
        leaveRoom(parseInt(room_id));
      }
    };
  }, [room_id]);

  // WebSocket消息处理
  useEffect(() => {
    if (!isConnected || !room_id) return;

    // 加入房间
    joinRoom(parseInt(room_id));
    if (user) {
      joinChatRoom(parseInt(room_id)).catch(err => {
        // 如果用户已在聊天室中，忽略错误（创建者会自动加入）
        const errorMessage = err.response?.data?.detail || err.message || '';
        if (errorMessage.includes('已在聊天室中')) {
          // 忽略"用户已在聊天室中"的错误
          return;
        }
        console.error('加入聊天室失败:', err);
      });
    }

    // 注册消息处理器
    const unsubscribe = onMessage((message) => {
      if (message.type === 'chat_message' && message.room_id === parseInt(room_id)) {
        // 收到新消息
        const newMessage: ChatMessage = {
          id: message.id,
          room_id: message.room_id,
          sender_id: message.sender_id,
          content: message.content,
          message_type: message.message_type,
          created_at: message.created_at,
          sender_username: message.sender_username || null,
        };
        setMessages(prev => [...prev, newMessage]);
      } else if (message.type === 'user_joined' && message.room_id === parseInt(room_id)) {
        // 用户加入通知
        console.log(`用户 ${message.user_id} 加入了房间`);
      } else if (message.type === 'user_left' && message.room_id === parseInt(room_id)) {
        // 用户离开通知
        console.log(`用户 ${message.user_id} 离开了房间`);
      }
    });

    return () => {
      unsubscribe();
      if (room_id && isConnected) {
        leaveRoom(parseInt(room_id));
      }
    };
  }, [isConnected, room_id, user]);

  const loadRoom = async () => {
    if (!room_id) return;

    try {
      const roomData = await getChatRoom(parseInt(room_id));
      setRoom(roomData);
    } catch (err: any) {
      setError(err.message || '加载聊天室失败');
    }
  };

  const loadMessages = async (page: number) => {
    if (!room_id) return;

    try {
      const response = await getChatRoomMessages(parseInt(room_id), page, pageSize);

      if (page === 1) {
        setMessages(response.messages);
      } else {
        setMessages(prev => [...response.messages, ...prev]);
      }

      setHasMore(response.messages.length === pageSize);
      setCurrentPage(page);
    } catch (err: any) {
      setError(err.message || '加载消息失败');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleLoadMore = () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    loadMessages(currentPage + 1);
  };

  const handleSendMessage = (content: string) => {
    if (!room_id || !isConnected) {
      setToast({ message: 'WebSocket未连接，无法发送消息', type: 'error' });
      return;
    }

    sendChatMessage(parseInt(room_id), content);
  };

  const openInviteModal = () => {
    if (room?.is_public) {
      setToast({ message: "公开聊天室不需要邀请", type: 'warning' });
      return;
    }
    setInviteUsername('');
    setInviteModalOpen(true);
  };

  const handleInviteSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault();
    if (!room_id || !inviteUsername.trim()) return;

    if (user && user.username === inviteUsername.trim()) {
      setToast({ message: "不能邀请自己", type: 'warning' });
      return;
    }

    setInviting(true);
    try {
      await inviteUserToRoom(parseInt(room_id), inviteUsername.trim());
      setToast({ message: `已成功邀请用户 ${inviteUsername}`, type: 'success' });
      setInviteModalOpen(false);
      loadRoom(); // Refresh room data to update member count
    } catch (err: any) {
      setToast({ message: err.response?.data?.detail || "邀请失败", type: 'error' });
    } finally {
      setInviting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <svg className="h-8 w-8 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span className="text-sm font-medium text-slate-600">加载中...</span>
        </div>
      </div>
    );
  }

  if (error && !room) {
    return (
      <div className="space-y-4">
        <div className="rounded-xl border border-red-200/80 bg-gradient-to-r from-red-50 to-red-50/50 px-4 py-3 text-sm text-red-700 shadow-soft">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-soft transition-smooth hover:border-slate-300 hover:bg-slate-50 hover:shadow-md"
          onClick={() => navigate('/chat')}
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回
        </button>
      </div>
    );
  }

  return (
    <div className="flex min-h-[70vh] flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200/80 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-soft transition-smooth hover:border-slate-300 hover:bg-slate-50 hover:shadow-md"
            onClick={() => navigate('/chat')}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            返回
          </button>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  {room?.name || '聊天室'}
                </h2>
                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-600">
                  <span className="flex items-center gap-1.5">
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    成员: {room?.member_count || 0}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1.5 font-semibold ${isConnected ? 'text-emerald-600' : 'text-slate-500'
                      }`}
                  >
                    <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`}></span>
                    <span>{isConnected ? '已连接' : '未连接'}</span>
                  </span>
                  {user && room?.creator_id === user.id && !room?.is_public && (
                    <button
                      type="button"
                      onClick={openInviteModal}
                      className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-600 hover:bg-blue-100 transition-colors"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                        <path d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z" />
                      </svg>
                      邀请
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200/80 bg-gradient-to-r from-red-50 to-red-50/50 px-4 py-3 text-sm text-red-700 shadow-soft">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}

      <ChatMessageList
        messages={messages}
        onLoadMore={handleLoadMore}
        hasMore={hasMore}
        loading={loadingMore}
      />

      <ChatInput onSend={handleSendMessage} placeholder="输入消息..." disabled={!isConnected} />

      {/* Modals and Toasts */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <Modal
        isOpen={inviteModalOpen}
        onClose={() => setInviteModalOpen(false)}
        title="邀请用户"
        footer={
          <>
            <button
              onClick={() => setInviteModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              disabled={inviting}
            >
              取消
            </button>
            <button
              onClick={handleInviteSubmit as any}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              disabled={inviting || !inviteUsername.trim()}
            >
              {inviting ? '邀请中...' : '提交'}
            </button>
          </>
        }
      >
        <div>
          <label htmlFor="invite-username" className="block text-sm font-medium text-gray-700 mb-2">
            用户名
          </label>
          <input
            type="text"
            id="invite-username"
            className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm"
            placeholder="请输入要邀请的用户名"
            value={inviteUsername}
            onChange={(e) => setInviteUsername(e.target.value)}
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter' && !inviting && inviteUsername.trim()) {
                handleInviteSubmit(e);
              }
            }}
          />
        </div>
      </Modal>
    </div>
  );
};

export default ChatRoomPage;
