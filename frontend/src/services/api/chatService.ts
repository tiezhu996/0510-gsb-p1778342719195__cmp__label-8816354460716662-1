/**
 * 聊天相关API服务
 */
import apiClient from './client';

// ========== 类型定义 ==========

export interface ChatRoom {
  id: number;
  name: string;
  description: string | null;
  creator_id: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  creator_username: string | null;
  member_count: number | null;
}

export interface ChatRoomCreate {
  name: string;
  description?: string;
  is_public?: boolean;
}

export interface ChatRoomListResponse {
  total: number;
  rooms: ChatRoom[];
  page: number;
  page_size: number;
}

export interface ChatMessage {
  id: number;
  room_id: number;
  sender_id: number;
  content: string;
  message_type: string;
  created_at: string;
  sender_username: string | null;
}

export interface ChatMessageListResponse {
  total: number;
  messages: ChatMessage[];
  page: number;
  page_size: number;
}

export interface PrivateMessage {
  id: number;
  sender_id: number;
  receiver_id: number;
  content: string;
  message_type: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  sender_username: string | null;
  receiver_username: string | null;
}

export interface PrivateMessageListResponse {
  total: number;
  messages: PrivateMessage[];
  page: number;
  page_size: number;
}

export interface Conversation {
  user_id: number;
  username: string;
  last_message: PrivateMessage | null;
  unread_count: number;
  last_message_at: string | null;
}

export interface ConversationListResponse {
  conversations: Conversation[];
}

// ========== API函数 ==========

/**
 * 获取聊天室列表
 */
export const getChatRooms = async (
  page: number = 1,
  pageSize: number = 20,
  userId?: number,
  isPublic?: boolean
): Promise<ChatRoomListResponse> => {
  const params: Record<string, string | number | boolean> = {
    page,
    page_size: pageSize,
  };
  if (userId) {
    params.user_id = userId;
  }
  if (isPublic !== undefined) {
    params.is_public = isPublic;
  }

  const response = await apiClient.get<ChatRoomListResponse>('/api/chat/rooms', { params });
  return response.data;
};

/**
 * 创建聊天室
 */
export const createChatRoom = async (data: ChatRoomCreate): Promise<ChatRoom> => {
  const response = await apiClient.post<ChatRoom>('/api/chat/rooms', data);
  return response.data;
};

/**
 * 获取聊天室详情
 */
export const getChatRoom = async (roomId: number): Promise<ChatRoom> => {
  const response = await apiClient.get<ChatRoom>(`/api/chat/rooms/${roomId}`);
  return response.data;
};

/**
 * 加入聊天室
 */
export const joinChatRoom = async (roomId: number): Promise<void> => {
  await apiClient.post(`/api/chat/rooms/${roomId}/join`);
};

/**
 * 离开聊天室
 */
export const leaveChatRoom = async (roomId: number): Promise<void> => {
  await apiClient.post(`/api/chat/rooms/${roomId}/leave`);
};


/**
 * 删除聊天室
 */
export const deleteChatRoom = async (roomId: number): Promise<void> => {
  await apiClient.delete(`/api/chat/rooms/${roomId}`);
};

/**
 * 邀请用户加入聊天室
 */
export const inviteUserToRoom = async (roomId: number, username: string): Promise<void> => {
  await apiClient.post(`/api/chat/rooms/${roomId}/invite`, { username });
};


/**
 * 获取聊天室消息历史
 */
export const getChatRoomMessages = async (
  roomId: number,
  page: number = 1,
  pageSize: number = 50
): Promise<ChatMessageListResponse> => {
  const params = {
    page,
    page_size: pageSize,
  };
  const response = await apiClient.get<ChatMessageListResponse>(
    `/api/chat/rooms/${roomId}/messages`,
    { params }
  );
  return response.data;
};

/**
 * 获取私聊会话列表
 */
export const getPrivateConversations = async (): Promise<ConversationListResponse> => {
  const response = await apiClient.get<ConversationListResponse>('/api/chat/private/conversations');
  return response.data;
};

/**
 * 获取私聊消息历史
 */
export const getPrivateMessages = async (
  userId: number,
  page: number = 1,
  pageSize: number = 50
): Promise<PrivateMessageListResponse> => {
  const params = {
    page,
    page_size: pageSize,
  };
  const response = await apiClient.get<PrivateMessageListResponse>(
    `/api/chat/private/${userId}/messages`,
    { params }
  );
  return response.data;
};

/**
 * 标记消息为已读
 */
export const markMessageRead = async (messageId: number): Promise<void> => {
  await apiClient.put(`/api/chat/private/messages/${messageId}/read`);
};

/**
 * 获取未读消息数量
 */
export const getUnreadCount = async (senderId?: number): Promise<{ unread_count: number }> => {
  const params = senderId ? { sender_id: senderId } : {};
  const response = await apiClient.get<{ unread_count: number }>(
    '/api/chat/private/unread-count',
    { params }
  );
  return response.data;
};

/**
 * 获取在线用户列表
 */
export const getOnlineUsers = async (): Promise<{ online_users: number[] }> => {
  const response = await apiClient.get<{ online_users: number[] }>('/api/chat/online-users');
  return response.data;
};

