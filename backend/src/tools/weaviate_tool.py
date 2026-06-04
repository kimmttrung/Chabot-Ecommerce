import os
import re
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from dotenv import load_dotenv
from crewai.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from weaviate.config import AdditionalConfig, Timeout

# 1. Định vị và load file .env chuẩn xác (lùi 1 cấp từ thư mục tools/ ra gốc backend)
current_dir = os.path.dirname(__file__)
env_path = os.path.abspath(os.path.join(current_dir, "../.env"))
load_dotenv(dotenv_path=env_path)

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

print("⏳ Chatbot đang tải mô hình nhúng HuggingFace (all-MiniLM-L6-v2)...")
hf_token = os.getenv("HF_TOKEN")
embeddings_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"token": hf_token} if hf_token else {}
)

# 2. KHỞI TẠO KẾT NỐI WEAVIATE TOÀN CỤC (GLOBAL CLIENT) - CHỈ CHẠY 1 LẦN KHI STARTUP
print("🔌 Chatbot đang thiết lập kết nối vĩnh viễn tới Weaviate Cloud v4...")
clean_domain = WEAVIATE_URL.strip().replace("https://", "").replace("http://", "").strip("/")
final_cluster_url = f"https://{clean_domain}"

weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=final_cluster_url,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY.strip()),
    skip_init_checks=True,
    additional_config=AdditionalConfig(
        timeout=Timeout(init=30, query=90, insert=120)  # Tăng thời gian chờ
    )
)


@tool("search_weaviate_tool")
def search_weaviate_tool(query: str) -> str:
    """
    Tìm kiếm sản phẩm trong cơ sở dữ liệu Weaviate dựa trên câu truy vấn của khách hàng.
    Hỗ trợ lọc theo giá (ví dụ: 'dưới 15 triệu') và tìm kiếm vector theo ngữ nghĩa.
    Trả về thông tin sản phẩm bao gồm tên, giá, thông số và link.
    """
    try:
        if not weaviate_client.is_connected():
            weaviate_client.connect()

        max_price = None
        price_match = re.search(r'(\d+)\s*(triệu|tr)', query.lower())
        filters = None
        clean_query = query
        if price_match:
            max_price = int(price_match.group(1)) * 1000000
            clean_query = re.sub(r'\d+\s*(triệu|tr|tầm dưới|dưới|tầm)', '', query, flags=re.IGNORECASE).strip()
            filters = Filter.by_property("price").less_or_equal(max_price)

        query_vector = embeddings_model.embed_query(clean_query)
        product_collection = weaviate_client.collections.get("Product")
        result = product_collection.query.near_vector(
            near_vector=query_vector,
            limit=3,
            filters=filters,
            return_properties=["name", "price", "url", "specifications"]
        )

        if not result or not result.objects:
            return "Hiện tại trong kho Phúc Anh không có dòng máy nào dưới tầm giá này hoặc đáp ứng được cấu hình bạn tìm. Quý khách có thể nâng ngân sách lên một chút được không ạ?"

        output = []
        for obj in result.objects:
            p = obj.properties
            price_raw = int(p['price']) if p.get('price') else 0
            price_formatted = f"{price_raw:,} VND" if price_raw else "Liên hệ"
            
            # An toàn với max_price = None
            if max_price is not None:
                budget_compare = 'Dưới ngân sách' if price_raw <= max_price else 'Vượt ngân sách'
                budget_line = f"- Giá so với ngân sách: {budget_compare}"
            else:
                budget_line = ""  # hoặc bỏ qua dòng này
            
            output.append(
                f"[SẢN PHẨM MẪU]\n"
                f"- Tên máy: {p.get('name')}\n"
                f"- Giá (VNĐ): {price_raw} (đã định dạng: {price_formatted})\n"
                f"{budget_line}\n"
                f"- Thông số: {p.get('specifications')}\n"
                f"- Link: {p.get('url')}"
            )
        return "\n\n".join(output)

    except Exception as e:
        return f"Lỗi xảy ra trong quá trình truy vấn Vector DB: {str(e)}"