# src/test_agent.py
import os
from dotenv import load_dotenv
# Nạp các biến môi trường từ file .env trước khi test
load_dotenv()

# Import hàm bạn muốn test trực tiếp
from craw import run_sales_agent

def debug_test():
    print("--- BẮT ĐẦU KIỂM TRA ĐỘC LẬP SALES AGENT ---")
    print(f"Kiểm tra API KEY: {os.getenv('GEMINI_API_KEY')[:10]}...")
    
    test_message = "Tôi muốn tìm một chiếc laptop gaming tầm giá 20 triệu"
    test_history = "User: Xin chào\nBot: Xin chào, tôi có thể giúp gì cho bạn?"
    
    try:
        # Chạy trực tiếp hàm để xem log Terminal xuất ra từ CrewAI (verbose=True)
        response = run_sales_agent(test_message, test_history)
        print("\n--- KẾT QUẢ PHẢN HỒI TỪ AGENT ---")
        print(response)
    except Exception as e:
        print("\n--- PHÁT HIỆN LỖI KHI CHẠY THỬ ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_test()