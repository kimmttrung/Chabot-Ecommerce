import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import các tiện ích quản lý Session
from utils.session_manager import (
    format_history_for_agent,
    get_or_create_session,
    save_chat_message,
)
# Import lớp Crew từ package agents
from my_agents.crew import MySalesCrew

# Load biến môi trường trước khi chạy server
load_dotenv()

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

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # 1. Xử lý Session (Trí nhớ ngắn hạn)
    session_id, history = get_or_create_session(request.session_id)

    # Lưu câu hỏi mới của khách vào lịch sử
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

    return {
        "session_id": session_id,
        "response": ai_response,
        "history": history,
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")

    # Đảm bảo chạy mượt mà ngay tại file main
    uvicorn.run("main:app", host=host, port=port, reload=True)