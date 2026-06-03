import os
import re
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from dotenv import load_dotenv
from crewai.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Định vị và load file .env chuẩn xác (lùi 1 cấp từ thư mục tools/ ra gốc backend)
current_dir = os.path.dirname(__file__)
env_path = os.path.abspath(os.path.join(current_dir, "../.env"))
load_dotenv(dotenv_path=env_path)

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

print("⏳ Chatbot đang tải mô hình nhúng HuggingFace (all-MiniLM-L6-v2)...")
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. KHỞI TẠO KẾT NỐI WEAVIATE TOÀN CỤC (GLOBAL CLIENT) - CHỈ CHẠY 1 LẦN KHI STARTUP
print("🔌 Chatbot đang thiết lập kết nối vĩnh viễn tới Weaviate Cloud v4...")
clean_domain = WEAVIATE_URL.strip().replace("https://", "").replace("http://", "").strip("/")
final_cluster_url = f"https://{clean_domain}"

weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=final_cluster_url,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY.strip()),
)

@tool("search_weaviate_tool")
def search_weaviate_tool(query: str) -> str:
    """Hàm này dùng để tìm kiếm sản phẩm dựa trên nhu cầu của khách hàng như cấu hình, tầm giá, tên máy."""
    try:
        # Tự động kết nối lại nếu kết nối toàn cục bị ngắt quãng ngầm
        if not weaviate_client.is_connected():
            weaviate_client.connect()

        # 1. Xử lý bộ lọc giá thông minh bằng Regex
        max_price = None
        price_match = re.search(r'(\d+)\s*(triệu|tr)', query.lower())

        filters = None
        clean_query = query
        if price_match:
            max_price = int(price_match.group(1)) * 1000000
            # Sửa câu query sạch để tạo vector chính xác (Ví dụ: "Samsung tầm dưới 5 triệu pin trâu" -> "Samsung pin trâu")
            clean_query = query.replace(price_match.group(0), "").replace("tầm dưới", "").replace("dưới", "").replace("tầm", "").strip()
            
            # CHÚ Ý PHẦN NÀY: Đổi từ less_than_equal thành less_or_equal chuẩn v4
            filters = Filter.by_property("price").less_or_equal(max_price)

        # 2. Tạo vector từ câu hỏi đã được làm sạch để tăng độ chính xác ngữ nghĩa
        query_vector = embeddings_model.embed_query(clean_query)
        
        # 3. Lấy collection Product để thực hiện truy vấn
        product_collection = weaviate_client.collections.get("Product")
        
        result = product_collection.query.near_vector(
            near_vector=query_vector,
            limit=3,
            filters=filters,
            return_properties=["name", "price", "url", "specifications"]
        )

        # Kiểm tra kết quả trả về từ đối tượng v4
        if not result or not result.objects:
            return "Hiện tại trong kho Phúc Anh không có dòng máy nào dưới tầm giá này hoặc đáp ứng được cấu hình bạn tìm. Quý khách có thể nâng ngân sách lên một chút được không ạ?"

        output = []
        for obj in result.objects:
            p = obj.properties
            price_raw = int(p['price']) if p.get('price') else 0
            price_formatted = f"{price_raw:,} VND" if price_raw else "Liên hệ"
            output.append(
                f"[SẢN PHẨM MẪU]\n"
                f"- Tên máy: {p.get('name')}\n"
                f"- Giá số thực tế: {price_raw} (Dạng hiển thị: {price_formatted})\n"
                f"- Thông số: {p.get('specifications')}\n"
                f"- Link: {p.get('url')}"
            )
        return "\n\n".join(output)

    except Exception as e:
        return f"Lỗi xảy ra trong quá trình truy vấn Vector DB: {str(e)}"