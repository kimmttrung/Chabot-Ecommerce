import os
from crewai import Agent, Crew, Process, Task
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.src.tools.weaviate_tool import search_weaviate_tool


def run_sales_agent(user_message: str, history_str: str) -> str:
    # Lấy API Key từ môi trường đã load ở config
    google_api_key = os.getenv("GEMINI_API_KEY")

    # Khởi tạo LLM cho Agent
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro", google_api_key=google_api_key, temperature=0.3
    )

    # 1. Tạo Sales Agent
    sales_agent = Agent(
        role="Chuyên viên tư vấn công nghệ Phúc Anh",
        goal="Dựa vào lịch sử trò chuyện và dữ liệu sản phẩm để tư vấn, gợi ý sản phẩm chính xác nhất cho khách hàng.",
        backstory="Bạn là một nhân viên bán hàng xuất sắc tại Phúc Anh Smart World. Bạn lịch sự, am hiểu phần cứng và luôn tìm sản phẩm đúng giá, đúng nhu cầu ẩn của khách.",
        tools=[search_weaviate_tool],  # Gọi Tool từ thư mục tools
        llm=llm,
        verbose=True,
    )

    # 2. Tạo Task tư vấn
    recommendation_task = Task(
        description=f"""
        Lịch sử trò chuyện trước đó:
        {history_str}
        
        Tin nhắn mới nhất của khách hàng: "{user_message}"
        
        Nhiệm vụ của bạn:
        1. Phân tích nhu cầu ẩn và khoảng giá khách mong muốn.
        2. Sử dụng tool 'Tìm kiếm sản phẩm điện thoại và máy tính Phúc Anh' để lấy dữ liệu thực tế.
        3. Đưa ra câu trả lời tư vấn thân thiện, có gợi ý kèm giá tiền và đường link sản phẩm.
        """,
        expected_output="Một đoạn hội thoại tư vấn bán hàng mượt mà, có gợi ý sản phẩm kèm link và giá cụ thể.",
        agent=sales_agent,
    )

    # 3. Kết nối vào Crew
    crew = Crew(
        agents=[sales_agent],
        tasks=[recommendation_task],
        process=Process.sequential,
    )

    result = crew.kickoff()
    return str(result)