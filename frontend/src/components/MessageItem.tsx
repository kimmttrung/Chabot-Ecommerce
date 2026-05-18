
import React from 'react';
import { User, Bot } from 'lucide-react';
import type { Message } from '../types/chat';

interface MessageItemProps {
    message: Message;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
    const isUser = message.sender === 'user';

    return (
        <div className={`py-6 border-b border-gray-100/50 dark:border-gray-800/30 ${isUser ? 'bg-white' : 'bg-gray-50'}`}>
            <div className="max-w-3xl mx-auto flex items-start gap-4 px-4">
                {/* Avatar */}
                <div className={`p-2 rounded-lg shrink-0 ${isUser ? 'bg-emerald-600 text-white' : 'bg-blue-600 text-white'}`}>
                    {isUser ? <User size={20} /> : <Bot size={20} />}
                </div>

                {/* Nội dung tin nhắn */}
                <div className="flex-1 space-y-1 pt-1">
                    <p className="text-xs font-semibold text-gray-400">
                        {isUser ? 'Bạn' : 'Sales AI Agent'}
                    </p>
                    <div className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
                        {message.text}
                    </div>
                </div>
            </div>
        </div>
    );
};