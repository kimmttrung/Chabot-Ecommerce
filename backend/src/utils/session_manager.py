import uuid

# Lưu trữ session trong RAM tạm thời
sessions_db = {}


def get_or_create_session(session_id: str = None):
    """Lấy lịch sử chat cũ hoặc tạo mới nếu chưa có session_id."""
    if not session_id or session_id not in sessions_db:
        session_id = str(uuid.uuid4())
        sessions_db[session_id] = []
    return session_id, sessions_db[session_id]


def save_chat_message(session_id: str, role: str, content: str):
    """Lưu tin nhắn của User hoặc AI vào lịch sử."""
    if session_id in sessions_db:
        sessions_db[session_id].append({"role": role, "content": content})


def format_history_for_agent(chat_history: list) -> str:
    """Biến đổi list hội thoại thành chuỗi text cho Agent dễ đọc bối cảnh."""
    # Bỏ qua tin nhắn cuối cùng vì đó chính là câu hỏi hiện tại
    return "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in chat_history[:-1]]
    )