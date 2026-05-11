import React, { useEffect } from 'react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastProps {
    message: string;
    type?: ToastType;
    onClose: () => void;
    duration?: number;
}

const Toast: React.FC<ToastProps> = ({
    message,
    type = 'info',
    onClose,
    duration = 3000
}) => {
    useEffect(() => {
        if (duration > 0) {
            const timer = setTimeout(() => {
                onClose();
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [duration, onClose]);

    if (!message) return null;

    return (
        <div className={`fixed top-8 left-1/2 transform -translate-x-1/2 z-[100] flex items-center px-4 py-3 bg-white rounded shadow-[0_3px_6px_-4px_rgba(0,0,0,0.12),0_6px_16px_0_rgba(0,0,0,0.08),0_9px_28px_8px_rgba(0,0,0,0.05)] border border-gray-100
      ${type === 'success' ? 'text-gray-800' : ''}
      ${type === 'error' ? 'text-gray-800' : ''}
      ${type === 'info' ? 'text-gray-800' : ''}
      ${type === 'warning' ? 'text-gray-800' : ''}`}
            role="alert"
        >
            <div className={`
        inline-flex items-center justify-center flex-shrink-0 w-4 h-4 mr-2
        ${type === 'success' ? 'text-green-500' : ''}
        ${type === 'error' ? 'text-red-500' : ''}
        ${type === 'info' ? 'text-blue-500' : ''}
        ${type === 'warning' ? 'text-yellow-500' : ''}
      `}>
                {type === 'success' && (
                    <svg className="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm3.707 8.207-4 4a1 1 0 0 1-1.414 0l-2-2a1 1 0 0 1 1.414-1.414L9 10.586l3.293-3.293a1 1 0 0 1 1.414 1.414Z" />
                    </svg>
                )}
                {type === 'error' && (
                    <svg className="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm3.707 11.793a1 1 0 1 1-1.414 1.414L10 11.414l-2.293 2.293a1 1 0 0 1-1.414-1.414L8.586 10 6.293 7.707a1 1 0 0 1 1.414-1.414L10 8.586l2.293-2.293a1 1 0 0 1 1.414 1.414L11.414 10l2.293 2.293Z" />
                    </svg>
                )}
                {type === 'info' && (
                    <svg className="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z" />
                    </svg>
                )}
                {type === 'warning' && (
                    <svg className="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM10 15a1 1 0 1 1 0-2 1 1 0 0 1 0 2Zm1-4a1 1 0 0 1-2 0V6a1 1 0 0 1 2 0v5Z" />
                    </svg>
                )}
            </div>
            <div className="text-sm font-normal select-none">{message}</div>

        </div>
    );
};

export default Toast;
