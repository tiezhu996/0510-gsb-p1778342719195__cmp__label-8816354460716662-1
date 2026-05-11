/**
 * 聊天消息列表组件
 */
import React, { useEffect, useRef } from 'react';
import ChatMessageItem from './ChatMessageItem';

interface Message {
  id: number;
  sender_id: number;
  sender_username: string | null;
  content: string;
  message_type: string;
  created_at: string;
  is_read?: boolean;
}

interface ChatMessageListProps {
  messages: Message[];
  onLoadMore?: () => void;
  hasMore?: boolean;
  loading?: boolean;
}

const ChatMessageList: React.FC<ChatMessageListProps> = ({
  messages,
  onLoadMore,
  hasMore = false,
  loading = false,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const prevScrollHeightRef = useRef<number>(0);

  // 自动滚动到底部（新消息）
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

  // 加载更多消息时保持滚动位置
  useEffect(() => {
    if (messagesContainerRef.current && prevScrollHeightRef.current > 0) {
      const container = messagesContainerRef.current;
      const scrollDiff = container.scrollHeight - prevScrollHeightRef.current;
      container.scrollTop += scrollDiff;
    }
    prevScrollHeightRef.current = messagesContainerRef.current?.scrollHeight || 0;
  }, [messages]);

  const handleScroll = () => {
    if (!messagesContainerRef.current || !onLoadMore || !hasMore || loading) {
      return;
    }

    const container = messagesContainerRef.current;
    if (container.scrollTop === 0) {
      prevScrollHeightRef.current = container.scrollHeight;
      onLoadMore();
    }
  };

  return (
    <div
      className="flex min-h-[60vh] flex-1 flex-col overflow-y-auto rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-sm p-4 shadow-elevated"
      ref={messagesContainerRef}
      onScroll={handleScroll}
    >
      {hasMore && (
        <div className="mb-4 flex items-center justify-center gap-2 rounded-xl bg-slate-50/80 px-4 py-2 text-xs font-medium text-slate-600">
          {loading ? (
            <>
              <svg className="h-4 w-4 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              加载中...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              滚动到顶部加载更多
            </>
          )}
        </div>
      )}
      {messages.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center py-16">
          <svg className="h-16 w-16 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <div className="mt-4 text-sm font-medium text-slate-500">暂无消息</div>
          <div className="mt-1 text-xs text-slate-400">开始发送第一条消息吧</div>
        </div>
      ) : (
        <div className="space-y-3">
          {messages.map((message) => (
            <ChatMessageItem
              key={message.id}
              id={message.id}
              senderId={message.sender_id}
              senderUsername={message.sender_username}
              content={message.content}
              messageType={message.message_type}
              createdAt={message.created_at}
              isRead={message.is_read}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  );
};

export default ChatMessageList;

