import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from tools.weaviate_tool import search_weaviate_tool

# Load biến môi trường từ file .env
load_dotenv()

@CrewBase
class MySalesCrew:
    """Hệ thống CrewAI xử lý Agentic RAG cho tư vấn bán hàng Phúc Anh"""

    # Đường dẫn tương đối từ vị trí file này (nằm trong thư mục agents) lùi ra ngoài để tìm config
    agents_config = '../config/agents.yaml'
    tasks_config = '../config/tasks.yaml'

    def __init__(self) -> None:
        # Khởi tạo bộ não LLM thông qua Groq
        self.llm = LLM(
            model="groq/llama-3.1-8b-instant",
            temperature=0.2
        )

    @agent
    def sales_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['sales_agent'],
            llm=self.llm,
            tools=[search_weaviate_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=10,
            respect_context_window=True,
            use_system_prompt=True,
            cache=False
        )

    @task
    def sales_task(self) -> Task:
        return Task(
            config=self.tasks_config['sales_task'],
            agent=self.sales_agent()
        )

    @crew
    def crew(self) -> Crew:
        """Khởi tạo cấu hình luồng chạy phối hợp"""
        return Crew(
            agents=self.agents,  # Tự động gom hàm có decorator @agent
            tasks=self.tasks,    # Tự động gom hàm có decorator @task
            process=Process.sequential,
            verbose=True
        )