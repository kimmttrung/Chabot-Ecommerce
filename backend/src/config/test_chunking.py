import os
import json
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_text(text):
    if not text:
        return ""
    
    # 1. Sửa dính chữ giữa chữ thường và chữ HOA (Ví dụ: "TớiPHÚC ANHan" -> "Tới PHÚC ANH an")
    text = re.sub(r'([a-zỳọáảãáạèéẻẽẹìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỹ])([A-ZĐ])', r'\1 \2', text)
    text = re.sub(r'([A-ZĐ])([A-ZĐ][a-zỳọáảãáạèéẻẽẹìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỹ])', r'\1 \2', text)
    
    # 2. Sửa dính chữ giữa chữ và số (Ví dụ: "kích thước167.4" -> "kích thước 167.4")
    text = re.sub(r'([a-zA-ZÀ-ỹ])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-ZÀ-ỹ])', r'\1 \2', text)
    
    # 3. Thêm khoảng trắng sau dấu câu nếu viết dính (Ví dụ: "rõ ràng.Thiết bị" -> "rõ ràng. Thiết bị")
    text = re.sub(r'(?<=[.!?])(?=[^\s])', r' ', text)
    
    # 4. Thu gọn nhiều khoảng trắng thừa liên tiếp
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def test_and_compare_chunks(json_path):
    if not os.path.exists(json_path):
        print(f"❌ Không tìm thấy file JSON tại: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    if not products:
        print("📭 File JSON trống.")
        return

    prod = products[0]
    prod_name = prod.get('name', 'N/A')
    specs_dict = prod.get("specifications", {})
    specs_str = ", ".join([f"{k}: {v}" for k, v in specs_dict.items()])
    description_raw = prod.get('description', '')

    # Tiến hành làm sạch dữ liệu dính chữ trước khi chunking
    description_cleaned = clean_text(description_raw)

    print("=" * 40)
    print("📋 [DỮ LIỆU SAU KHI LÀM SẠCH TEXT DÍNH CHỮ]")
    print("=" * 40)
    print(f"🔹 Nội dung sạch:\n{description_cleaned}")
    print("\n" + "=" * 40)

    # Cấu hình bộ cắt tối ưu: Ưu tiên ngắt ở chấm câu trước để câu văn của Agent không bị què cụt
    chunk_size = 500 
    chunk_overlap = 100

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        keep_separator=True
    )

    desc_chunks = text_splitter.split_text(description_cleaned)

    print(f"✂️ [KẾT QUẢ CHUNKING CHUẨN] -> Chia làm {len(desc_chunks)} Chunks")
    print("=" * 40)

    for i, chunk in enumerate(desc_chunks):
        final_text_to_embedding = (
            f"Tên sản phẩm: {prod_name}. "
            f"Thông số: {specs_str}. "
            f"Mô tả (Phần {i+1}): {chunk}"
        )
        
        print(f"▶️ [CHUNK #{i+1}] (Độ dài: {len(final_text_to_embedding)} ký tự)")
        print(f"--- Đoạn text cắt ra: ---")
        print(chunk)
        print(f"----------------------------------")
        print(f"💡 Chuỗi đầy đủ để đưa vào Vector DB:")
        print(f"👉 \"{final_text_to_embedding[:120]} ... {final_text_to_embedding[-60:]}\"")
        print("-" * 50)

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    json_absolute_path = os.path.abspath(os.path.join(current_dir, "../../phucanh_samsung_products.json"))
    test_and_compare_chunks(json_absolute_path)