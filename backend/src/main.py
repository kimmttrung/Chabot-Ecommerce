import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import các module từ cấu trúc thư mục mới
from utils.session_manager import (
    format_history_for_agent,
    get_or_create_session,
    save_chat_message,
)
from craw import run_sales_agent
# Load biến môi trường trước khi server chạy
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
    # 1. Xử lý Session (Trí nhớ ngắn hạn) thông qua Utils
    session_id, history = get_or_create_session(request.session_id)

    # Lưu câu hỏi mới của khách vào lịch sử
    save_chat_message(session_id, "user", request.message)

    # Định dạng lịch sử chat thành chuỗi để ném vào Agent
    history_str = format_history_for_agent(history)

    # 2. Gọi bộ não CrewAI xử lý Agentic RAG
    ai_response = run_sales_agent(request.message, history_str)

    # 3. Lưu câu trả lời của AI vào lịch sử cho lần sau
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

    uvicorn.run("main:app", host=host, port=port, reload=True)