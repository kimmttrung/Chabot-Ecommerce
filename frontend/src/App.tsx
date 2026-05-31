import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import type { ChatSession, Message } from './types/chat';

function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([
    { id: '1', title: 'Tư vấn mua Laptop Gaming', messages: [] }
  ]);
  const [activeSessionId, setActiveSessionId] = useState<string>('1');

  const activeSession = sessions.find(s => s.id === activeSessionId);

  // Tạo Session mới
  const handleCreateSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: `Cuộc trò chuyện mới`,
      messages: []
    };
    setSessions([newSession, ...sessions]);
    setActiveSessionId(newSession.id);
  };

  // Xóa Session
  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Tránh kích hoạt sự kiện chọn Session
    const filtered = sessions.filter(s => s.id !== id);
    setSessions(filtered);
    if (activeSessionId === id && filtered.length > 0) {
      setActiveSessionId(filtered[0].id);
    }
  };

  // Gửi tin nhắn và gọi API Backend
  const handleSendMessage = async (text: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date()
    };

    // 1. Cập nhật tin nhắn của User vào UI ngay lập tức
    let updatedSessions = sessions.map(session => {
      if (session.id === activeSessionId) {
        // Tự đổi tiêu đề chat dựa trên câu hỏi đầu tiên
        const title = session.messages.length === 0 ? (text.length > 20 ? text.substring(0, 20) + '...' : text) : session.title;
        return {
          ...session,
          title,
          messages: [...session.messages, userMsg]
        };
      }
      return session;
    });
    setSessions(updatedSessions);

    try {
      // 2. Gọi API tới Backend FastAPi/Flask (Ví dụ: cổng 8000)
      // Truyền kèm `session_id` để Backend xử lý lưu bộ nhớ (Weaviate/Redis)
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: activeSessionId
        }),
      });
      const data = await response.json();

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: data.response || 'Xin lỗi, tôi gặp sự cố khi xử lý thông tin.',
        timestamp: new Date()
      };

      // 3. Cập nhật phản hồi của Bot vào đúng Session
      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, messages: [...s.messages, botMsg] };
        }
        return s;
      }));

    } catch (error) {
      console.error("Lỗi kết nối Backend:", error);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-100">
      <Sidebar
        sessions={sessions}
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