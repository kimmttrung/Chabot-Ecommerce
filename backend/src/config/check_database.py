import os
import weaviate
from dotenv import load_dotenv

# Tìm file .env lùi ra 2 cấp
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),
)

print("--- KIỂM TRA VECTOR DATABASE WEAVIATE ---")

try:
    meta_result = client.query.aggregate("Product").with_meta_count().do()
    count = meta_result["data"]["Aggregate"]["Product"][0]["meta"]["count"]
    print(f"📊 Tổng số sản phẩm hiện có trên DB: {count} sản phẩm.")
except Exception as e:
    print(f"Không thể lấy tổng số lượng: {e}")

print("\n📋 Hiển thị thử 3 sản phẩm ngẫu nhiên trong DB:")
try:
    sample_result = client.query.get(
        "Product", ["name", "price", "specifications"]
    ).with_limit(3).do()
    
    products_list = sample_result["data"]["Get"]["Product"]
    for i, p in enumerate(products_list):
        print(f"\n[{i+1}] {p['name']}")
        print(f"   - Giá: {p['price']:,} VNĐ")
        print(f"   - Cấu hình: {p['specifications'][:80]}...")
except Exception as e:
    print(f"Không thể truy vấn lấy mẫu: {e}")