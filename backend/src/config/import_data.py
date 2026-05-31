import os
import json
import weaviate
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# Load cấu hình
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# 1. Khởi tạo mô hình Embedding chạy LOCAL (Không cần API Key Google)
print("⏳ Đang tải mô hình nhúng HuggingFace về máy (chỉ tải lần đầu)...")
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Khởi tạo kết nối Weaviate
weaviate_client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
)

class_obj = {
    "class": "Product",
    "description": "Danh sách điện thoại Samsung từ Phúc Anh Smart World",
    "vectorizer": "none",
    "properties": [
        {"name": "name", "dataType": ["text"], "description": "Tên điện thoại"},
        {"name": "url", "dataType": ["string"], "description": "Link sản phẩm"},
        {"name": "price", "dataType": ["int"], "description": "Giá bán hiện tại"},
        {"name": "old_price", "dataType": ["int"], "description": "Giá cũ"},
        {"name": "description", "dataType": ["text"], "description": "Bài viết mô tả chi tiết"},
        {"name": "specifications", "dataType": ["text"], "description": "Thông số kỹ thuật gộp"},
        {"name": "image_url", "dataType": ["string"], "description": "Ảnh sản phẩm"}
    ]
}

# Kiểm tra và làm sạch Schema trước khi nạp
try:
    current_schema = weaviate_client.schema.get()
    class_exists = any(c["class"] == "Product" for c in current_schema.get("classes", []))
    
    # Nếu bảng cũ lỗi đang tồn tại, xóa đi để reset lại số chiều vector mới cho khớp với HuggingFace
    if class_exists:
        weaviate_client.schema.delete_class("Product")
        print("🗑️ Đã xóa bảng 'Product' cũ để đồng bộ cấu trúc mới.")
        
    weaviate_client.schema.create_class(class_obj)
    print("🎉 Đã khởi tạo cấu trúc bảng 'Product' mới thành công!")
except Exception as e:
    print(f"❌ Lỗi khi khởi tạo Schema: {e}")


def import_products_to_weaviate(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"🚀 Bắt đầu quá trình nạp {len(products)} sản phẩm vào Vector DB...")

    with weaviate_client.batch(batch_size=20) as batch:
        for idx, prod in enumerate(products):
            try:
                specs_dict = prod.get("specifications", {})
                specs_str = ", ".join([f"{k}: {v}" for k, v in specs_dict.items()])
                
                text_to_vectorize = (
                    f"Tên sản phẩm: {prod.get('name')}. "
                    f"Thông số: {specs_str}. "
                    f"Mô tả chi tiết: {prod.get('description')}"
                )
                
                # Tạo vector local cực nhanh
                vector_embedding = embeddings_model.embed_query(text_to_vectorize)

                properties = {
                    "name": prod.get("name"),
                    "url": prod.get("url"),
                    "price": int(prod.get("price", 0)) if prod.get("price") else 0,
                    "old_price": int(prod.get("old_price", 0)) if prod.get("old_price") else 0,
                    "description": prod.get("description"),
                    "specifications": specs_str,
                    "image_url": prod.get("image_url")
                }

                batch.add_data_object(
                    data_object=properties,
                    class_name="Product",
                    vector=vector_embedding
                )
                print(f" -> Đã import thành công mẫu số {idx+1}/{len(products)}: {prod.get('name')[:30]}...")
            except Exception as inner_e:
                print(f"❌ Lỗi tại dòng {idx}: {inner_e}")

    print("✨ Hoàn tất quá trình nạp dữ liệu!")

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    json_absolute_path = os.path.abspath(os.path.join(current_dir, "../../phucanh_samsung_products.json"))
    import_products_to_weaviate(json_absolute_path)