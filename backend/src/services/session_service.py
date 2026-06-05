# services/session_service.py
import uuid
from typing import List, Dict, Tuple, Optional
from services.database import get_db_connection

def get_or_create_session(session_id: Optional[str] = None) -> Tuple[str, List[Dict[str, str]]]:
    """Trả về (session_id, history)"""
    conn = get_db_connection()
    with conn.cursor() as cur:
        if session_id:
            cur.execute("SELECT session_id FROM sessions WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
            if not row:
                # Tạo session mới với ID do client cung cấp
                cur.execute("INSERT INTO sessions (session_id) VALUES (%s)", (session_id,))
                conn.commit()
        else:
            session_id = str(uuid.uuid4())
            cur.execute("INSERT INTO sessions (session_id) VALUES (%s)", (session_id,))
            conn.commit()
        
        # Lấy lịch sử tin nhắn
        cur.execute("""
            SELECT role, content FROM messages 
            WHERE session_id = %s 
            ORDER BY timestamp ASC
        """, (session_id,))
        rows = cur.fetchall()
        history = [{"role": row["role"], "content": row["content"]} for row in rows]
    
    conn.close()
    return session_id, history

def save_chat_message(session_id: str, role: str, content: str):
    """Lưu tin nhắn và cập nhật title nếu là tin nhắn đầu tiên của user"""
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Đếm số tin nhắn hiện có của session này
        cur.execute("SELECT COUNT(*) AS cnt FROM messages WHERE session_id = %s", (session_id,))
        row = cur.fetchone()
        count = row['cnt'] if row else 0
        
        # Lưu tin nhắn mới
        cur.execute("""
            INSERT INTO messages (session_id, role, content)
            VALUES (%s, %s, %s)
        """, (session_id, role, content))
        
        # Nếu là tin nhắn đầu tiên và là user -> cập nhật title
        if count == 0 and role == 'user':
            # Lấy tối đa 50 ký tự đầu (hoặc 5 từ - bạn có thể thay logic)
            title = content[:50].strip()
            if not title:
                title = "Cuộc trò chuyện mới"
            cur.execute("UPDATE sessions SET title = %s, updated_at = NOW() WHERE session_id = %s", (title, session_id))
        else:
            # Chỉ cập nhật updated_at
            cur.execute("UPDATE sessions SET updated_at = NOW() WHERE session_id = %s", (session_id,))
        
        conn.commit()
    conn.close()

def get_all_sessions() -> List[Dict]:
    """Lấy danh sách tất cả sessions, sắp xếp theo updated_at mới nhất"""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT session_id, title, created_at, updated_at 
            FROM sessions 
            ORDER BY updated_at DESC
        """)
        rows = cur.fetchall()
        sessions = [
            {
                "id": row["session_id"],
                "title": row["title"] or "Chưa có tiêu đề",
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat()
            }
            for row in rows
        ]
    conn.close()
    return sessions

def delete_session(session_id: str):
    """Xóa toàn bộ session và messages liên quan (cascade)"""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        conn.commit()
    conn.close()

def format_history_for_agent(history: List[Dict], max_turns: int = 10) -> str:
    """Giữ nguyên như cũ"""
    if not history:
        return "Chưa có hội thoại trước đó."
    recent = history[-max_turns*2:] if len(history) > max_turns*2 else history
    lines = []
    for msg in recent:
        prefix = "Khách hàng" if msg['role'] == 'user' else "Tư vấn viên"
        lines.append(f"{prefix}: {msg['content']}")
    return "\n".join(lines)