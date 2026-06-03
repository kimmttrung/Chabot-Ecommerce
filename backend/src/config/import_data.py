import os
import json
import re
import weaviate
import weaviate.classes.config as wc
from weaviate.classes.init import Auth
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Định vị chính xác file .env lùi 2 cấp từ vị trí của file import_data.py
current_dir = os.path.dirname(__file__)
env_path = os.path.abspath(os.path.join(current_dir, "../../.env"))
load_dotenv(dotenv_path=env_path)

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# Hàm xử lý làm sạch dính chữ và số chuyên sâu của bạn
def clean_text(text):
    if not text: 
        return ""
    # Sửa dính chữ thường và chữ HOA (Ví dụ: "TớiPHÚC" -> "Tới PHÚC")
    text = re.sub(r'([a-zỳọáảãáạèéẻẽẹìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỹ])([A-ZĐ])', r'\1 \2', text)
    text = re.sub(r'([A-ZĐ])([A-ZĐ][a-zỳọáảãáạèéẻẽẹìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỹ])', r'\1 \2', text)
    # Sửa dính chữ và số (Ví dụ: "kích thước167.4" -> "kích thước 167.4")
    text = re.sub(r'([a-zA-ZÀ-ỹ])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-ZÀ-ỹ])', r'\1 \2', text)
    # Sửa dính dấu câu
    text = re.sub(r'(?<=[.!?])(?=[^\s])', r' ', text)
    # Thu gọn khoảng trắng thừa
    return re.sub(r'\s+', ' ', text).strip()

# 2. Khởi tạo mô hình Embedding chạy LOCAL (all-MiniLM-L6-v2)
print("⏳ Đang khởi tạo mô hình nhúng HuggingFace (all-MiniLM-L6-v2)...")
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 3. Chuẩn hóa URL để bảo vệ kết nối luôn đúng định dạng v4
# Dù bạn truyền URL có hay không có https://, hàm này vẫn dọn sạch và ép về dạng https:// chuẩn cho Weaviate Cloud
clean_domain = WEAVIATE_URL.strip().replace("https://", "").replace("http://", "").strip("/")
final_cluster_url = f"https://{clean_domain}"

print(f"🔌 Đang kết nối tới Weaviate Cloud v4: {final_cluster_url}")
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=final_cluster_url,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY.strip()),
)

# Kiểm tra xem cụm đã kết nối mượt mà chưa
if client.is_ready():
    print("✅ Đã kết nối thành công tới Weaviate Cloud v4 mới tinh!")
else:
    print("❌ Không thể kết nối. Vui lòng kiểm tra lại Cluster Status trên Console WCD.")

# 4. Tạo cấu trúc bảng dữ liệu (Collection) theo chuẩn v4 mới
collection_name = "Product"
try:
    # Nếu bảng Product cũ đang tồn tại, tiến hành xóa sạch để đồng bộ lại số chiều Vector
    if client.collections.exists(collection_name):
        client.collections.delete(collection_name)
        print(f"🗑️ Đã xóa bảng '{collection_name}' cũ thành công.")

    # Khởi tạo bảng với kiểu dữ liệu chuẩn v4
    client.collections.create(
        name=collection_name,
        description="Danh sách sản phẩm công nghệ từ hệ thống Phúc Anh",
        vectorizer_config=None, # Tự nạp Vector Embedding chạy local
        properties=[
            wc.Property(name="name", data_type=wc.DataType.TEXT, description="Tên sản phẩm"),
            wc.Property(name="url", data_type=wc.DataType.TEXT, description="Link sản phẩm"),
            wc.Property(name="price", data_type=wc.DataType.INT, description="Giá bán hiện tại"),
            wc.Property(name="old_price", data_type=wc.DataType.INT, description="Giá cũ"),
            wc.Property(name="description", data_type=wc.DataType.TEXT, description="Bài viết mô tả chi tiết được chunking"),
            wc.Property(name="specifications", data_type=wc.DataType.TEXT, description="Thông số kỹ thuật gộp"),
            wc.Property(name="image_url", data_type=wc.DataType.TEXT, description="Ảnh sản phẩm")
        ]
    )
    print(f"🎉 Khởi tạo cấu trúc bảng '{collection_name}' v4 thành công!")
except Exception as e:
    print(f"❌ Lỗi khi thiết lập Schema: {e}")


def import_products_to_weaviate(json_path):
    if not os.path.exists(json_path):
        print(f"❌ Lỗi: Không tìm thấy file JSON tại đường dẫn: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Cấu hình bộ Text Splitter cắt câu thông minh dựa trên kết quả test của bạn
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        keep_separator=True
    )

    print(f"🚀 Bắt đầu Chunking dữ liệu & nạp {len(products)} sản phẩm vào DB...")
    
    # Lấy thực thể collection để thực hiện cơ chế nạp Batch
    product_collection = client.collections.get(collection_name)

    # Sử dụng cơ chế nạp Dynamic Batching cực mạnh của phiên bản v4
    with product_collection.batch.dynamic() as batch:
        for idx, prod in enumerate(products):
            try:
                specs_dict = prod.get("specifications", {})
                specs_str = ", ".join([f"{k}: {v}" for k, v in specs_dict.items()])
                prod_name = prod.get('name', 'N/A')
                
                # Tạo chuỗi thông tin nền để làm giàu ngữ cảnh (Tránh mất liên kết Tên - Cấu hình khi cắt nhỏ)
                base_info = f"Tên sản phẩm: {prod_name}. Thông số: {specs_str}."
                description_raw = prod.get('description', '')
                
                # Tiến hành dọn dẹp dính chữ và chia khối văn bản nhỏ
                description_cleaned = clean_text(description_raw)
                desc_chunks = text_splitter.split_text(description_cleaned)
                
                if not desc_chunks:
                    desc_chunks = [""]

                # Lặp qua từng chunk nhỏ đã cắt để embedding và lưu vào DB
                for c_idx, chunk in enumerate(desc_chunks):
                    text_to_vectorize = f"{base_info} Mô tả (Phần {c_idx+1}): {chunk}"
                    
                    # Tiến hành tạo Vector Embedding local
                    vector_embedding = embeddings_model.embed_query(text_to_vectorize)

                    properties = {
                        "name": prod_name,
                        "url": prod.get("url"),
                        "price": int(prod.get("price", 0)) if prod.get("price") else 0,
                        "old_price": int(prod.get("old_price", 0)) if prod.get("old_price") else 0,
                        "description": text_to_vectorize, # Lưu lại khối text đầy đủ ngữ cảnh để LLM đọc
                        "specifications": specs_str,
                        "image_url": prod.get("image_url")
                    }

                    # Cú pháp nạp Object kèm Vector đặc trưng cực ngắn gọn của v4
                    batch.add_object(
                        properties=properties,
                        vector=vector_embedding
                    )
                print(f" -> Đã băm nhỏ & Nạp thành công sản phẩm {idx+1}/{len(products)}: {prod_name[:20]}...")
            except Exception as inner_e:
                print(f"❌ Lỗi xử lý tại sản phẩm ở index {idx}: {inner_e}")

    print("✨ Quá trình nạp dữ liệu hoàn tất hoàn hảo! Đang giải phóng tài nguyên...")
    client.close()

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    json_absolute_path = os.path.abspath(os.path.join(current_dir, "../../phucanh_samsung_products.json"))
    import_products_to_weaviate(json_absolute_path)