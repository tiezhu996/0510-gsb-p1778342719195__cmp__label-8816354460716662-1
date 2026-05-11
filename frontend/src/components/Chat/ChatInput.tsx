/**
 * 聊天输入组件
 */
import React, { useState, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (content: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, placeholder = '输入消息...', disabled = false }) => {
  const [content, setContent] = useState<string>('');

  const handleSend = () => {
    if (content.trim() && !disabled) {
      onSend(content.trim());
      setContent('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex items-end gap-3 rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-sm p-4 shadow-elevated">
      <textarea
        className="min-h-[48px] flex-1 resize-none rounded-xl border border-slate-200/80 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 shadow-soft transition-smooth focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:shadow-md disabled:bg-slate-50 disabled:text-slate-500"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={2}
      />
      <button
        type="button"
        className="gradient-primary hover:gradient-primary-hover inline-flex h-[48px] items-center justify-center gap-2 rounded-xl px-6 text-sm font-semibold text-white shadow-lg transition-smooth hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:shadow-lg"
        onClick={handleSend}
        disabled={disabled || !content.trim()}
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
        发送
      </button>
    </div>
  );
};

export default ChatInput;

