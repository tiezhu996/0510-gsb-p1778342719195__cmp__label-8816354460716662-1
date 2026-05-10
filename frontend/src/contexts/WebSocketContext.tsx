/**
 * WebSocket上下文
 */
import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { wsService, MessageHandler } from '../services/websocket';

interface WebSocketContextType {
  isConnected: boolean;
  connectionState: string;
  sendChatMessage: (roomId: number, content: string, messageType?: string) => void;
  sendPrivateMessage: (receiverId: number, content: string, messageType?: string) => void;
  joinRoom: (roomId: number) => void;
  leaveRoom: (roomId: number) => void;
  onMessage: (handler: MessageHandler) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('CLOSED');

  // 连接WebSocket
  useEffect(() => {
    if (isAuthenticated && user) {
      wsService.connect(user.id)
        .then(() => {
          setIsConnected(true);
          setConnectionState(wsService.connectionState);
        })
        .catch((error) => {
          console.error('WebSocket连接失败:', error);
          setIsConnected(false);
          setConnectionState('CLOSED');
        });
    } else {
      // 用户未登录，断开连接
      wsService.disconnect();
      setIsConnected(false);
      setConnectionState('CLOSED');
    }

    // 清理函数
    return () => {
      if (!isAuthenticated || !user) {
        wsService.disconnect();
      }
    };
  }, [isAuthenticated, user]);

  // 监听连接状态变化
  useEffect(() => {
    const checkConnection = setInterval(() => {
      const connected = wsService.isConnected;
      const state = wsService.connectionState;
      
      setIsConnected(connected);
      setConnectionState(state);
    }, 1000);

    return () => clearInterval(checkConnection);
  }, []);

  // 发送群聊消息
  const sendChatMessage = useCallback((roomId: number, content: string, messageType: string = 'text') => {
    wsService.sendChatMessage(roomId, content, messageType);
  }, []);

  // 发送私聊消息
  const sendPrivateMessage = useCallback((receiverId: number, content: string, messageType: string = 'text') => {
    wsService.sendPrivateMessage(receiverId, content, messageType);
  }, []);

  // 加入房间
  const joinRoom = useCallback((roomId: number) => {
    wsService.joinRoom(roomId);
  }, []);

  // 离开房间
  const leaveRoom = useCallback((roomId: number) => {
    wsService.leaveRoom(roomId);
  }, []);

  // 注册消息处理器
  const onMessage = useCallback((handler: MessageHandler) => {
    return wsService.onMessage(handler);
  }, []);

  const value: WebSocketContextType = {
    isConnected,
    connectionState,
    sendChatMessage,
    sendPrivateMessage,
    joinRoom,
    leaveRoom,
    onMessage,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

