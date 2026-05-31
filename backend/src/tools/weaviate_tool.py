import os
import weaviate
from dotenv import load_dotenv
from crewai.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Load biến môi trường từ file .env ở thư mục gốc (lùi 1 cấp từ tools/)
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# 2. KHỞI TẠO MÔ HÌNH NHÚNG LOCAL (Phải trùng khớp hoàn toàn với file import_data)
# Chạy local 100% không lo API Key Google bị block hay lỗi endpoint v1beta nữa
print("⏳ Chatbot đang tải mô hình nhúng HuggingFace (all-MiniLM-L6-v2)...")
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 3. Khởi tạo kết nối Weaviate
weaviate_client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
)

@tool("search_weaviate_tool")
def search_weaviate_tool(query: str) -> str:
    """Hàm này dùng để tìm kiếm sản phẩm dựa trên nhu cầu của khách hàng như cấu hình, tầm giá, tên máy."""
    try:
        query_vector = embeddings_model.embed_query(query)

        # Logic thông minh: Tự động phát hiện bộ lọc giá nếu trong câu query có số tiền
        # Ví dụ khách gõ "10 triệu" hoặc "10tr" -> đoán khoảng 10,000,000
        max_price = None
        import re
        price_match = re.search(r'(\d+)\s*(triệu|tr)', query.lower())
        if price_match:
            max_price = int(price_match.group(1)) * 1000000

        # Khởi tạo câu lệnh truy vấn Weaviate
        query_builder = weaviate_client.query.get("Product", ["name", "price", "url", "specifications"])
        
        # Nếu có bộ lọc giá thì ép cứng điều kiện toán học (Lọc sản phẩm <= túi tiền của khách)
        if max_price:
            query_builder = query_builder.with_where({
                "path": ["price"],
                "operator": "LessThanEqual",
                "valueInt": max_price
            })

        result = (
            query_builder
            .with_near_vector({"vector": query_vector})
            .with_limit(3)
            .do()
        )

        if not result or "data" not in result or not result["data"]["Get"]["Product"]:
            return "Hiện tại trong kho Phúc Anh không có dòng Samsung nào dưới tầm giá này đáp ứng được cấu hình pin trâu. Bạn có muốn nâng ngân sách lên chút không?"

        products = result["data"]["Get"]["Product"]
        
        output = []
        for p in products:
            price_formatted = f"{p['price']:,} VND" if p['price'] else "Liên hệ"
            output.append(
                f"- Tên: {p['name']}\n"
                f"  Giá: {price_formatted}\n"
                f"  Thông số: {p['specifications']}\n"
                f"  Link: {p['url']}"
            )
        return "\n\n".join(output)

    except Exception as e:
        return f"Lỗi xảy ra trong quá trình truy vấn Vector DB: {str(e)}"