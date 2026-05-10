/**
 * 私聊页面
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { 
  getPrivateMessages,
  markMessageRead,
  PrivateMessage
} from '../services/api/chatService';
import ChatMessageList from '../components/Chat/ChatMessageList';
import ChatInput from '../components/Chat/ChatInput';

const PrivateChatPage: React.FC = () => {
  const { user_id } = useParams<{ user_id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isConnected, sendPrivateMessage, onMessage } = useWebSocket();
  
  const [messages, setMessages] = useState<PrivateMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [receiverUsername, setReceiverUsername] = useState<string>('用户');
  const pageSize = 50;

  useEffect(() => {
    if (user_id && user) {
      // 检查是否是尝试与自己私聊
      if (parseInt(user_id) === user.id) {
        setError('不能与自己私聊');
        setLoading(false);
        return;
      }
      loadMessages(1);
    }
  }, [user_id, user]);

  // WebSocket消息处理
  useEffect(() => {
    if (!isConnected || !user_id || !user) return;

    // 注册消息处理器
    const unsubscribe = onMessage((message) => {
      if (message.type === 'private_message') {
        const receiverId = message.receiver_id || message.sender_id;
        const targetUserId = parseInt(user_id);
        
        // 只处理与当前对话用户相关的消息
        if (
          (message.sender_id === targetUserId && receiverId === user.id) ||
          (message.sender_id === user.id && receiverId === targetUserId)
        ) {
          const newMessage: PrivateMessage = {
            id: message.id,
            sender_id: message.sender_id,
            receiver_id: receiverId,
            content: message.content,
            message_type: message.message_type,
            is_read: message.is_read || false,
            read_at: message.read_at || null,
            created_at: message.created_at,
            sender_username: message.sender_username || null,
            receiver_username: message.receiver_username || null,
          };
          
          setMessages(prev => [...prev, newMessage]);
          
          // 如果是接收到的消息，标记为已读
          if (message.receiver_id === user.id && !message.is_read) {
            markMessageRead(message.id).catch(err => {
              console.error('标记消息已读失败:', err);
            });
          }
        }
      }
    });

    return unsubscribe;
  }, [isConnected, user_id, user]);

  // 标记消息为已读
  useEffect(() => {
    if (!user_id || !user || messages.length === 0) return;

    const unreadMessages = messages.filter(
      msg => msg.receiver_id === user.id && !msg.is_read
    );

    unreadMessages.forEach(msg => {
      markMessageRead(msg.id).catch(err => {
        console.error('标记消息已读失败:', err);
      });
    });
  }, [messages, user_id, user]);

  const loadMessages = async (page: number) => {
    if (!user_id || !user) return;
    
    try {
      const response = await getPrivateMessages(parseInt(user_id), page, pageSize);
      
      if (page === 1) {
        setMessages(response.messages);
        // 获取接收者用户名
        if (response.messages.length > 0) {
          const firstMessage = response.messages[0];
          const receiver = firstMessage.sender_id === user.id 
            ? firstMessage.receiver_username 
            : firstMessage.sender_username;
          setReceiverUsername(receiver || '用户');
        }
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
    if (!user_id || !isConnected) {
      setError('WebSocket未连接，无法发送消息');
      return;
    }
    
    sendPrivateMessage(parseInt(user_id), content);
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
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-cyan-600 text-lg font-bold text-white shadow-lg">
                {receiverUsername?.[0]?.toUpperCase() || 'U'}
              </div>
              <div>
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  与 {receiverUsername} 的私聊
                </h2>
                <div className="mt-2 text-xs text-slate-600">
                  <span
                    className={`inline-flex items-center gap-1.5 font-semibold ${
                      isConnected ? 'text-emerald-600' : 'text-slate-500'
                    }`}
                  >
                    <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`}></span>
                    <span>{isConnected ? '已连接' : '未连接'}</span>
                  </span>
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
        messages={messages.map((msg) => ({
          id: msg.id,
          sender_id: msg.sender_id,
          sender_username: msg.sender_username,
          content: msg.content,
          message_type: msg.message_type,
          created_at: msg.created_at,
          is_read: msg.is_read,
        }))}
        onLoadMore={handleLoadMore}
        hasMore={hasMore}
        loading={loadingMore}
      />

      <ChatInput onSend={handleSendMessage} placeholder="输入消息..." disabled={!isConnected} />
    </div>
  );
};

export default PrivateChatPage;

