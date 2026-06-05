// src/App.tsx
import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { useSessions } from './hooks/useSessions';
import { chatApi } from './services/api';
import type { ChatSession, Message } from './types/chat';

function App() {
  const { sessions, loading, createSession, deleteSession, fetchSessions } = useSessions();
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [sessionMessages, setSessionMessages] = useState<Record<string, Message[]>>({});

  // Khi sessions thay đổi, chọn active session đầu tiên nếu chưa có
  useEffect(() => {
    let newActiveId = activeSessionId;

    if (sessions.length === 0) {
      newActiveId = '';
    } else if (!sessions.some(s => s.id === activeSessionId)) {
      // Nếu activeSessionId hiện tại không còn trong danh sách (do xóa hoặc reset)
      newActiveId = sessions[0].id;
    }

    // Chỉ set state khi thực sự khác, tránh render vô ích
    if (newActiveId !== activeSessionId) {
      setActiveSessionId(newActiveId);
    }
  }, [sessions, activeSessionId]);

  const chatSessions: ChatSession[] = sessions.map(s => ({
    id: s.id,
    title: s.title,
    messages: sessionMessages[s.id] || [],
  }));

  const activeSession = chatSessions.find(s => s.id === activeSessionId);

  const handleCreateSession = async () => {
    const newId = await createSession();
    if (newId) setActiveSessionId(newId);
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const success = await deleteSession(id);
    if (success && activeSessionId === id) {
      const remaining = sessions.filter(s => s.id !== id);
      setActiveSessionId(remaining.length > 0 ? remaining[0].id : '');
    }
    setSessionMessages(prev => {
      const newMap = { ...prev };
      delete newMap[id];
      return newMap;
    });
  };

  const handleSendMessage = async (text: string) => {
    if (!activeSessionId) return;

    // Optimistic user message
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date(),
    };
    setSessionMessages(prev => ({
      ...prev,
      [activeSessionId]: [...(prev[activeSessionId] || []), userMsg],
    }));

    try {
      const data = await chatApi.send(activeSessionId, text);
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: data.response,
        timestamp: new Date(),
      };
      setSessionMessages(prev => ({
        ...prev,
        [activeSessionId]: [...(prev[activeSessionId] || []), botMsg],
      }));
      if (data.title) fetchSessions(); // cập nhật title mới lên sidebar
    } catch (error) {
      console.error(error);
      const errorMsg: Message = {
        id: (Date.now() + 2).toString(),
        sender: 'bot',
        text: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.',
        timestamp: new Date(),
      };
      setSessionMessages(prev => ({
        ...prev,
        [activeSessionId]: [...(prev[activeSessionId] || []), errorMsg],
      }));
    }
  };

  if (loading) return <div className="flex items-center justify-center h-screen">Đang tải...</div>;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-100">
      <Sidebar
        sessions={chatSessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
      />
      <ChatArea
        currentSession={activeSession}
        onSendMessage={handleSendMessage}
      />
    </div>
  );
}

export default App;