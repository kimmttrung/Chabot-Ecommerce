import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { MessageItem } from './MessageItem';
import type { ChatSession } from '../types/chat';

interface ChatAreaProps {
    currentSession: ChatSession | undefined;
    onSendMessage: (text: string) => void;
}

export const ChatArea: React.FC<ChatAreaProps> = ({ currentSession, onSendMessage }) => {
    const [input, setInput] = useState('');
    const bottomRef = useRef<HTMLDivElement>(null);

    // Tự động cuộn xuống khi có tin nhắn mới
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [currentSession?.messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;
        onSendMessage(input);
        setInput('');
    };

    if (!currentSession) {
        return (
            <div className="flex-1 flex items-center justify-center bg-white text-gray-400">
                Hãy chọn hoặc tạo một cuộc trò chuyện mới để bắt đầu tư vấn.
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col h-screen bg-white">
            {/* Danh sách Message */}
            <div className="flex-1 overflow-y-auto">
                {currentSession.messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 p-4">
                        <h2 className="text-xl font-semibold mb-2 text-gray-700">Tôi có thể giúp gì cho bạn hôm nay?</h2>
                        <p className="text-sm max-w-md text-center">Hệ thống AI tích hợp Weaviate và CrewAI đã sẵn sàng tìm kiếm sản phẩm và tư vấn bán hàng.</p>
                    </div>
                ) : (
                    currentSession.messages.map((msg) => <MessageItem key={msg.id} message={msg} />)
                )}
                <div ref={bottomRef} />
            </div>

            {/* Form Input nhập tin nhắn */}
            <div className="p-4 border-t border-gray-100 max-w-3xl w-full mx-auto">
                <form onSubmit={handleSubmit} className="relative flex items-center">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Hỏi về sản phẩm, giá cả, thông số..."
                        className="w-full pl-4 pr-12 py-3 border border-gray-300 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm shadow-sm"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim()}
                        className="absolute right-2 p-2 bg-blue-600 disabled:bg-gray-200 text-white disabled:text-gray-400 rounded-lg transition hover:bg-blue-700"
                    >
                        <Send size={16} />
                    </button>
                </form>
                <p className="text-center text-xs text-gray-400 mt-2">
                    Sales Agent có thể đưa ra câu trả lời dựa trên dữ liệu sản phẩm thực tế từ Weaviate.
                </p>
            </div>
        </div>
    );
};