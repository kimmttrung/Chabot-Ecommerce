import React from 'react';
import { MessageSquare, Plus, Trash2, Bot } from 'lucide-react';
import type { ChatSession } from '../types/chat';

interface SidebarProps {
    sessions: ChatSession[];
    activeSessionId: string;
    onSelectSession: (id: string) => void;
    onCreateSession: () => void;
    onDeleteSession: (id: string, e: React.MouseEvent) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
    sessions,
    activeSessionId,
    onSelectSession,
    onCreateSession,
    onDeleteSession
}) => {
    return (
        <div className="w-64 bg-gray-900 text-gray-200 flex flex-col h-screen border-r border-gray-800">
            {/* Nút New Chat */}
            <div className="p-3">
                <button
                    onClick={onCreateSession}
                    className="w-full flex items-center gap-2 p-3 border border-gray-700 rounded-lg hover:bg-gray-800 transition text-sm font-medium"
                >
                    <Plus size={16} />
                    Cuộc trò chuyện mới
                </button>
            </div>

            {/* Danh sách Sessions */}
            <div className="flex-1 overflow-y-auto px-3 space-y-1">
                <p className="text-xs text-gray-500 font-semibold px-2 mb-2">Gần đây</p>
                {sessions.map((session) => (
                    <div
                        key={session.id}
                        onClick={() => onSelectSession(session.id)}
                        className={`flex items-center justify-between p-3 rounded-lg cursor-pointer group text-sm transition ${session.id === activeSessionId ? 'bg-gray-800 text-white' : 'hover:bg-gray-800/50 text-gray-400'
                            }`}
                    >
                        <div className="flex items-center gap-2 overflow-hidden">
                            <MessageSquare size={16} className="shrink-0" />
                            <span className="truncate">{session.title}</span>
                        </div>
                        <button
                            onClick={(e) => onDeleteSession(session.id, e)}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 rounded transition"
                        >
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
            </div>

            {/* Footer chứa thông tin User/Dự án */}
            <div className="p-4 border-t border-gray-800 flex items-center gap-3">
                <div className="bg-blue-600 p-2 rounded-full text-white">
                    <Bot size={20} />
                </div>
                <div>
                    <p className="text-sm font-medium text-white">E-Commerce Bot</p>
                    <p className="text-xs text-gray-400">Sales Agent Crew</p>
                </div>
            </div>
        </div>
    );
};