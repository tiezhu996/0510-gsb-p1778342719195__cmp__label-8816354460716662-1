/**
 * 聊天主页
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import {
  getChatRooms,
  createChatRoom,
  getPrivateConversations,
  getOnlineUsers,
  ChatRoom,
  Conversation,
  ChatRoomCreate,
  deleteChatRoom
} from '../services/api/chatService';

import Modal from '../components/ui/Modal';
import Toast, { ToastType } from '../components/ui/Toast';

const ChatHomePage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const { onMessage } = useWebSocket();
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<number[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  // Create Room State
  const [showCreateRoom, setShowCreateRoom] = useState<boolean>(false);
  const [roomName, setRoomName] = useState<string>('');
  const [roomDescription, setRoomDescription] = useState<string>('');
  const [isPublic, setIsPublic] = useState<boolean>(true);
  const [creating, setCreating] = useState<boolean>(false);

  // Delete Modal State
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [roomToDelete, setRoomToDelete] = useState<{ id: number, name: string } | null>(null);

  // Toast State
  const [toast, setToast] = useState<{ message: string, type: ToastType } | null>(null);

  // 使用 useCallback 优化函数，避免不必要的重新创建
  const loadConversations = useCallback(async () => {
    try {
      const response = await getPrivateConversations();
      setConversations(response.conversations);
    } catch (err: any) {
      console.error('加载私聊会话失败:', err);
    }
  }, []);

  const loadRooms = useCallback(async () => {
    try {
      // 获取聊天室列表（后端会根据用户登录状态自动返回合适的列表）
      // - 未登录：只返回公开聊天室
      // - 已登录：返回公开聊天室 + 用户加入的非公开聊天室
      const response = await getChatRooms(1, 20);
      setRooms(response.rooms);
    } catch (err: any) {
      console.error('加载聊天室失败:', err);
    }
  }, []);

  const loadOnlineUsers = useCallback(async () => {
    try {
      const response = await getOnlineUsers();
      setOnlineUsers(response.online_users);
    } catch (err: any) {
      console.error('加载在线用户失败:', err);
    }
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      await Promise.all([
        loadRooms(),
        loadConversations(),
        loadOnlineUsers()
      ]);
    } catch (err: any) {
      setError(err.message || '加载数据失败');
    } finally {
      setLoading(false);
    }
  }, [loadRooms, loadConversations, loadOnlineUsers]);

  useEffect(() => {
    // 确保用户已登录后再加载数据
    if (user) {
      loadData();
      // 定期刷新在线用户列表和会话列表
      const interval = setInterval(() => {
        loadOnlineUsers();
        loadConversations(); // 定期刷新会话列表，以便显示新的私聊会话
      }, 5000); // 每5秒刷新一次

      return () => clearInterval(interval);
    }
  }, [user, loadData, loadOnlineUsers, loadConversations]);

  // 当路由变化到聊天主页时，刷新会话列表
  useEffect(() => {
    if (user && location.pathname === '/chat') {
      loadConversations();
    }
  }, [location.pathname, user, loadConversations]);

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roomName.trim()) {
      setToast({ message: '聊天室名称不能为空', type: 'error' });
      return;
    }

    setCreating(true);
    setError('');
    try {
      const roomData: ChatRoomCreate = {
        name: roomName.trim(),
        description: roomDescription.trim() || undefined,
        is_public: isPublic,
      };
      const newRoom = await createChatRoom(roomData);
      setRooms([newRoom, ...rooms]);
      setRoomName('');
      setRoomDescription('');
      setIsPublic(true);
      setShowCreateRoom(false);
      setToast({ message: '聊天室创建成功', type: 'success' });
      navigate(`/chat/room/${newRoom.id}`);
    } catch (err: any) {
      setToast({ message: err.message || '创建聊天室失败', type: 'error' });
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, roomId: number, roomName: string) => {
    e.stopPropagation();
    setRoomToDelete({ id: roomId, name: roomName });
    setDeleteModalOpen(true);
  };

  const confirmDeleteRoom = async () => {
    if (!roomToDelete) return;

    try {
      await deleteChatRoom(roomToDelete.id);
      setRooms(prev => prev.filter(r => r.id !== roomToDelete.id));
      setToast({ message: '聊天室已删除', type: 'success' });
    } catch (err: any) {
      setToast({ message: err.message || '删除聊天室失败', type: 'error' });
    } finally {
      setDeleteModalOpen(false);
      setRoomToDelete(null);
    }
  };

  // 监听WebSocket消息，处理实时邀请
  useEffect(() => {
    const unsubscribe = onMessage((message: any) => {
      if (message.type === 'room_invited') {
        setToast({ message: `你被邀请加入聊天室: ${message.room_name}`, type: 'info' });
        loadRooms();
      } else if (message.type === 'room_deleted') {
        setRooms((prev: ChatRoom[]) => prev.filter((r: ChatRoom) => r.id !== message.room_id));
        setToast({ message: '你所在的聊天室已被解散', type: 'warning' });
      }
    });

    return () => {
      unsubscribe();
    };
  }, [onMessage, loadRooms]);

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

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">聊天中心</h1>
          <p className="mt-1 text-sm text-slate-600">选择聊天室或开始私聊</p>
        </div>
        <button
          type="button"
          className="gradient-primary hover:gradient-primary-hover inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition-smooth hover:shadow-xl"
          onClick={() => setShowCreateRoom(!showCreateRoom)}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {showCreateRoom ? '取消' : '创建聊天室'}
        </button>
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

      {showCreateRoom && (
        <div className="rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-sm p-6 shadow-elevated transition-smooth">
          <h2 className="mb-5 flex items-center gap-2 text-lg font-bold text-slate-900">
            <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            创建聊天室
          </h2>
          <form onSubmit={handleCreateRoom} className="space-y-5">
            <div>
              <label htmlFor="room-name" className="mb-2 block text-sm font-semibold text-slate-700">
                聊天室名称 <span className="text-red-600">*</span>
              </label>
              <input
                id="room-name"
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                required
                placeholder="输入聊天室名称"
                maxLength={100}
                className="mt-1 w-full rounded-xl border border-slate-300/80 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 shadow-soft transition-smooth focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:shadow-md"
              />
            </div>

            <div>
              <label htmlFor="room-description" className="mb-2 block text-sm font-semibold text-slate-700">
                描述（可选）
              </label>
              <textarea
                id="room-description"
                value={roomDescription}
                onChange={(e) => setRoomDescription(e.target.value)}
                placeholder="输入聊天室描述"
                rows={3}
                className="mt-1 w-full resize-none rounded-xl border border-slate-300/80 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 shadow-soft transition-smooth focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:shadow-md"
              />
            </div>

            <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 text-sm font-medium text-slate-700 transition-smooth hover:bg-slate-50">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/20"
              />
              公开聊天室
            </label>

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                className="inline-flex items-center rounded-xl border border-slate-200/80 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-soft transition-smooth hover:border-slate-300 hover:bg-slate-50 hover:shadow-md disabled:opacity-60"
                onClick={() => {
                  setShowCreateRoom(false);
                  setRoomName('');
                  setRoomDescription('');
                  setError('');
                }}
                disabled={creating}
              >
                取消
              </button>
              <button
                type="submit"
                className="gradient-primary hover:gradient-primary-hover inline-flex items-center rounded-xl px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition-smooth hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:shadow-lg"
                disabled={creating || !roomName.trim()}
              >
                {creating ? (
                  <>
                    <svg className="mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    创建中...
                  </>
                ) : (
                  '创建'
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <section className="rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-sm p-6 shadow-elevated">
          <div className="mb-5 flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h2 className="text-lg font-bold text-slate-900">聊天室</h2>
          </div>
          {rooms.length === 0 ? (
            <div className="rounded-xl border-2 border-dashed border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100/50 p-12 text-center">
              <svg className="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <div className="mt-4 text-sm font-medium text-slate-600">暂无聊天室</div>
              <button
                type="button"
                className="gradient-primary hover:gradient-primary-hover mt-4 inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition-smooth hover:shadow-xl"
                onClick={() => setShowCreateRoom(true)}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                创建第一个聊天室
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {rooms.map((room) => (
                <button
                  key={room.id}
                  type="button"
                  className="group w-full rounded-xl border border-slate-200/80 bg-white p-5 text-left shadow-soft transition-smooth hover:border-blue-300 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-slate-50 hover:shadow-md"
                  onClick={() => navigate(`/chat/room/${room.id}`)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <div className="text-base font-bold text-slate-900 group-hover:text-blue-700 transition-colors">
                          {room.name}
                        </div>
                      </div>
                      {room.description && (
                        <div className="mt-2 text-sm text-slate-600 line-clamp-2">{room.description}</div>
                      )}
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold shadow-sm ${room.is_public
                        ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white'
                        : 'bg-slate-100 text-slate-700'
                        }`}
                    >
                      {room.is_public ? '公开' : '私有'}
                    </span>
                    {user && room.creator_id === user.id && (
                      <div
                        role="button"
                        tabIndex={0}
                        className="ml-2 shrink-0 rounded-full from-red-500 to-red-600 p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                        onClick={(e) => handleDeleteClick(e, room.id, room.name)}
                        title="删除聊天室"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            handleDeleteClick(e as any, room.id, room.name);
                          }
                        }}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      创建者: {room.creator_username || '未知'}
                    </span>
                    <span className="flex items-center gap-1">
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      成员: {room.member_count || 0}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <aside className="space-y-6">
          <section className="rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-sm p-6 shadow-elevated">
            <div className="mb-5 flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600">
                <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h2 className="text-lg font-bold text-slate-900">私聊会话</h2>
            </div>
            {conversations.length === 0 ? (
              <div className="rounded-xl bg-slate-50/50 p-8 text-center">
                <div className="text-sm font-medium text-slate-500">暂无私聊会话</div>
              </div>
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <button
                    key={conv.user_id}
                    type="button"
                    className="group w-full rounded-xl border border-slate-200/80 bg-white p-4 text-left shadow-soft transition-smooth hover:border-blue-300 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-slate-50 hover:shadow-md"
                    onClick={() => navigate(`/chat/private/${conv.user_id}`)}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-xs font-bold text-white shadow-md">
                          {conv.username?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div className="text-sm font-bold text-slate-900 group-hover:text-blue-700 transition-colors">
                          {conv.username}
                        </div>
                      </div>
                      {conv.unread_count > 0 && (
                        <span className="inline-flex min-w-[24px] items-center justify-center rounded-full bg-gradient-to-r from-red-500 to-red-600 px-2 py-1 text-xs font-bold text-white shadow-md">
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                    {conv.last_message && (
                      <div className="mt-3 text-xs text-slate-600">
                        <div className="line-clamp-2">{conv.last_message.content}</div>
                        {conv.last_message_at && (
                          <div className="mt-2 text-[11px] text-slate-500">
                            {new Date(conv.last_message_at).toLocaleString()}
                          </div>
                        )}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-sm p-6 shadow-elevated">
            <div className="mb-5 flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600">
                <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
                </svg>
              </div>
              <h2 className="text-lg font-bold text-slate-900">
                在线用户 <span className="ml-2 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">{onlineUsers.length}</span>
              </h2>
            </div>
            {onlineUsers.length === 0 ? (
              <div className="rounded-xl bg-slate-50/50 p-8 text-center">
                <div className="text-sm font-medium text-slate-500">暂无在线用户</div>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {onlineUsers.map((userId) => (
                  <button
                    key={userId}
                    type="button"
                    className="group inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-soft transition-smooth hover:border-blue-300 hover:bg-gradient-to-r hover:from-blue-50 hover:to-slate-50 hover:shadow-md"
                    onClick={() => navigate(`/chat/private/${userId}`)}
                    title="点击发起私聊"
                  >
                    <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                    {userId === user?.id ? '我' : `用户 ${userId}`}
                  </button>
                ))}
              </div>
            )}
          </section>
        </aside>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="确认删除"
        footer={
          <>
            <button
              onClick={() => setDeleteModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              取消
            </button>
            <button
              onClick={confirmDeleteRoom}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              确认删除
            </button>
          </>
        }
      >
        <p className="text-sm text-gray-500">
          确定要删除聊天室 "{roomToDelete?.name}" 吗？
          <br />
          此操作不可恢复，所有消息将被清空。
        </p>
      </Modal>
    </div>
  );
};

export default ChatHomePage;
