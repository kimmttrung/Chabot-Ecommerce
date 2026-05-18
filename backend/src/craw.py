import os
from dotenv import load_dotenv          # Thêm dòng này
from crewai import Agent, Crew, Process, Task, LLM
from config.database import weaviate_client
from tools.weaviate_tool import search_weaviate_tool

# Load biến môi trường từ file .env
load_dotenv()                           # Đọc file .env ở thư mục gốc

def run_sales_agent(message: str, history_str: str) -> str:

    # --- Phần 2: Khởi tạo LLM với Groq (có tiền tố "groq/") ---
    try:
        llm = LLM(
            model="groq/llama-3.1-8b-instant",   # THÊM "groq/" phía trước
            temperature=0.2
        )
        print("LLM Groq khởi tạo thành công!")
    except Exception as e:
        print(f"Lỗi khởi tạo LLM: {e}")
        return "Có lỗi xảy ra khi kết nối tới Groq."

    # --- Phần 3: Agent, Task, Crew ---
    sales_agent = Agent(
        role="Chuyên viên tư vấn công nghệ Phúc Anh",
        goal="Dựa trên nhu cầu khách hàng và kho dữ liệu sản phẩm để tư vấn sản phẩm công nghệ chính xác nhất",
        backstory=(
            "Bạn là một chuyên gia am hiểu sâu sắc về các dòng laptop, linh kiện điện tử tại Phúc Anh. "
            "Bạn có phong cách tư vấn chuyên nghiệp, lịch sự và luôn hướng tới việc giải quyết bài toán của khách hàng."
        ),
        llm=llm,
        tools=[search_weaviate_tool],    # Bỏ comment nếu muốn dùng tool
        verbose=True,
        allow_delegation=False,
        max_iter=15,
        respect_context_window=True,
        use_system_prompt=True
    )

    sales_task = Task(
        description=(
            f"Khách hàng đang hỏi: '{message}'.\n"
            f"Lịch sử các câu thoại trước đó: \n{history_str}\n"
            "Hãy sử dụng công cụ tra cứu dữ liệu (search_weaviate_tool) để tìm các sản phẩm thực tế có trong kho "
            "phù hợp với yêu cầu của khách (nếu cần thông tin về thông số hoặc giá cả). Sau đó đưa ra câu trả lời thuyết phục."
        ),
        expected_output="Một câu trả lời tư vấn bán hàng đầy đủ, thân thiện, có gợi ý tên sản phẩm cụ thể kèm giá và thông số nếu tìm thấy.",
        agent=sales_agent
    )

    sales_crew = Crew(
        agents=[sales_agent],
        tasks=[sales_task],
        process=Process.sequential,
        verbose=True
    )

    result = sales_crew.kickoff()
    return str(result)