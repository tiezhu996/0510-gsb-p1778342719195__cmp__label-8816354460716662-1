/**
 * 聊天消息项组件
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface ChatMessageItemProps {
  id: number;
  senderId: number;
  senderUsername: string | null;
  content: string;
  messageType: string;
  createdAt: string;
  isRead?: boolean;
}

const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  senderId,
  senderUsername,
  content,
  createdAt,
  isRead,
}) => {
  const { user } = useAuth();
  const isOwnMessage = user?.id === senderId;

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}小时前`;
    
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`flex gap-3 ${isOwnMessage ? 'justify-end' : 'justify-start'}`}>
      {!isOwnMessage && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-slate-400 to-slate-500 text-xs font-bold text-white shadow-md">
          {senderUsername?.[0]?.toUpperCase() || 'U'}
        </div>
      )}
      <div className={`flex max-w-[75%] flex-col ${isOwnMessage ? 'items-end' : 'items-start'}`}>
        {!isOwnMessage && (
          <div className="mb-1.5 text-xs font-semibold text-slate-700">
            {senderUsername || '未知用户'}
          </div>
        )}

        <div
          className={`group rounded-2xl px-4 py-2.5 shadow-md transition-smooth ${
            isOwnMessage 
              ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white' 
              : 'bg-white border border-slate-200/80 text-slate-900'
          }`}
        >
          <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">{content}</div>
          <div
            className={`mt-2 flex items-center gap-2 text-[11px] ${
              isOwnMessage ? 'text-blue-100' : 'text-slate-500'
            }`}
          >
            <span className="font-medium">{formatTime(createdAt)}</span>
            {isRead !== undefined && isOwnMessage && (
              <span className={`flex items-center gap-1 ${isRead ? 'text-blue-200' : 'text-blue-300'}`}>
                {isRead ? (
                  <>
                    <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    已读
                  </>
                ) : (
                  '未读'
                )}
              </span>
            )}
          </div>
        </div>
      </div>
      {isOwnMessage && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-xs font-bold text-white shadow-md">
          {user?.username?.[0]?.toUpperCase() || '我'}
        </div>
      )}
    </div>
  );
};

export default ChatMessageItem;

