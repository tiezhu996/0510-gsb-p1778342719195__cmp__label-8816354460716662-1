/**
 * WebSocket服务
 * 管理WebSocket连接和消息
 */
import { WS_URL } from '../utils/constants';
import { getToken } from '../utils/helpers';

export type MessageType = 
  | 'chat_message'
  | 'private_message'
  | 'join_room'
  | 'leave_room'
  | 'room_joined'
  | 'room_left'
  | 'user_joined'
  | 'user_left'
  | 'connection'
  | 'message_sent'
  | 'error'
  | 'ping'
  | 'pong';

export interface WebSocketMessage {
  type: MessageType;
  [key: string]: any;
}

export type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private userId: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3秒
  // 浏览器环境下 setTimeout/setInterval 返回值不是 NodeJS.Timeout
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private isConnecting = false;

  /**
   * 连接WebSocket
   */
  connect(userId: number): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('正在连接中...'));
        return;
      }

      this.userId = userId;
      this.isConnecting = true;

      const token = getToken();
      if (!token) {
        this.isConnecting = false;
        reject(new Error('未找到Token，请先登录'));
        return;
      }

      const wsUrl = `${WS_URL}/ws/${userId}?token=${token}`;
      
      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket连接已建立');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('解析WebSocket消息失败:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error);
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket连接已关闭');
          this.isConnecting = false;
          this.stopHeartbeat();
          this.attemptReconnect();
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    this.stopHeartbeat();
    this.clearReconnectTimer();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.userId = null;
    this.reconnectAttempts = 0;
  }

  /**
   * 发送消息
   */
  send(message: WebSocketMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket未连接，无法发送消息');
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
    }
  }

  /**
   * 发送群聊消息
   */
  sendChatMessage(roomId: number, content: string, messageType: string = 'text'): void {
    this.send({
      type: 'chat_message',
      room_id: roomId,
      content,
      message_type: messageType,
    });
  }

  /**
   * 发送私聊消息
   */
  sendPrivateMessage(receiverId: number, content: string, messageType: string = 'text'): void {
    this.send({
      type: 'private_message',
      receiver_id: receiverId,
      content,
      message_type: messageType,
    });
  }

  /**
   * 加入房间
   */
  joinRoom(roomId: number): void {
    this.send({
      type: 'join_room',
      room_id: roomId,
    });
  }

  /**
   * 离开房间
   */
  leaveRoom(roomId: number): void {
    this.send({
      type: 'leave_room',
      room_id: roomId,
    });
  }

  /**
   * 注册消息处理器
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    
    // 返回取消注册函数
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    // 调用所有注册的处理器
    this.messageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('消息处理器出错:', error);
      }
    });
  }

  /**
   * 尝试重连
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('达到最大重连次数，停止重连');
      return;
    }

    if (!this.userId) {
      return;
    }

    this.reconnectAttempts++;
    console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    this.reconnectTimer = setTimeout(() => {
      if (this.userId) {
        this.connect(this.userId).catch(error => {
          console.error('重连失败:', error);
        });
      }
    }, this.reconnectDelay);
  }

  /**
   * 清除重连定时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * 开始心跳检测
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({
          type: 'ping',
          timestamp: Date.now(),
        });
      }
    }, 30000); // 每30秒发送一次心跳
  }

  /**
   * 停止心跳检测
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 获取连接状态字符串
   */
  get connectionState(): string {
    if (!this.ws) return 'CLOSED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }
}

// 导出单例
export const wsService = new WebSocketService();

