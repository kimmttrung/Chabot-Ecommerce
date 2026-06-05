import os
import uuid
from dotenv import load_dotenv

# 1. ĐƯA LÊN ĐẦU: Load biến môi trường ngay lập tức khi ứng dụng khởi chạy
load_dotenv()

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 2. Bây giờ mới import các service (lúc này các service đã đọc được env chuẩn)
from services.session_service import get_or_create_session, save_chat_message, format_history_for_agent, get_all_sessions, delete_session
from services.database import init_db, get_db_connection
from my_agents.crew import MySalesCrew

# init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code ở đây chỉ chạy 1 lần duy nhất khi Worker bắt đầu
    init_db() 
    yield

app = FastAPI(title="Agentic RAG E-Commerce Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str = None
    message: str

@app.get("/api/sessions")
async def list_sessions():
    """Lấy danh sách tất cả phiên chat"""
    sessions = get_all_sessions()
    return {"sessions": sessions}

@app.post("/api/sessions")
async def create_new_session():
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO sessions (session_id, title) VALUES (%s, %s)", (session_id, "Cuộc trò chuyện mới"))
        conn.commit()
    conn.close()
    return {"session_id": session_id, "title": "Cuộc trò chuyện mới"}

@app.delete("/api/sessions/{session_id}")
async def remove_session(session_id: str):
    """Xóa một phiên chat"""
    delete_session(session_id)
    return {"message": "Session deleted"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # 1. Xử lý Session (Trí nhớ ngắn hạn)
    session_id, history = get_or_create_session(request.session_id)

    # Lưu câu hỏi mới của user vào lịch sử
    save_chat_message(session_id, "user", request.message)

    # Định dạng lịch sử chat thành chuỗi cho Agent đọc hiểu bối cảnh cuộc hội thoại
    history_str = format_history_for_agent(history)

    # 2. Đóng gói dữ liệu đầu vào khớp với các biến {message} và {history_str} trong file yaml
    inputs = {
        "message": request.message,
        "history_str": history_str
    }
    
    try:
        # Khởi tạo thực thể bộ khung Crew và tiến hành kích hoạt luồng xử lý
        sales_crew_instance = MySalesCrew().crew()
        result = sales_crew_instance.kickoff(inputs=inputs)
        ai_response = str(result)
    except Exception as e:
        print(f"Lỗi khi thực thi CrewAI: {e}")
        ai_response = "Xin lỗi quý khách, hệ thống đang gặp sự cố gián đoạn. Vui lòng thử lại sau ít phút."

    # 3. Lưu câu trả lời của AI vào lịch sử cho lần hội thoại kế tiếp
    save_chat_message(session_id, "assistant", ai_response)

    # Sau khi lưu tin nhắn, lấy lại thông tin session để lấy title mới (nếu có)
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT title FROM sessions WHERE session_id = %s", (session_id,))
        row = cur.fetchone()
        title = row["title"] if row else None
    conn.close()

    return {
        "session_id": session_id,
        "response": ai_response,
        "title": title,
        "history": history + [{"role": "assistant", "content": ai_response}]
    }



if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")

    # Đảm bảo chạy mượt mà ngay tại file main
    uvicorn.run("main:app", host=host, port=port, reload=True)