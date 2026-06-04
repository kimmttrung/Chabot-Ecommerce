import os
import socket
import weaviate
from dotenv import load_dotenv
from weaviate.classes.init import Auth
from urllib.parse import urlparse

# Load .env
current_dir = os.path.dirname(__file__)
env_path = os.path.abspath(os.path.join(current_dir, "../../.env"))
load_dotenv(dotenv_path=env_path)

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

print("=" * 60)
print("📡 KIỂM TRA KẾT NỐI WEAVIATE")
print("=" * 60)
print(f"WEAVIATE_URL raw    : '{WEAVIATE_URL}'")
print(f"WEAVIATE_API_KEY    : '{WEAVIATE_API_KEY[:10] if WEAVIATE_API_KEY else 'None'}...'")

if not WEAVIATE_URL or not WEAVIATE_API_KEY:
    print("❌ Thiếu WEAVIATE_URL hoặc WEAVIATE_API_KEY trong .env")
    exit(1)

# Chuẩn hóa URL: giữ nguyên nếu đã có https://, nếu không thì thêm
url_raw = WEAVIATE_URL.strip()
if not url_raw.startswith(("http://", "https://")):
    final_cluster_url = f"https://{url_raw}"
else:
    final_cluster_url = url_raw

print(f"Final cluster URL  : {final_cluster_url}")

# Lấy hostname để kiểm tra DNS
parsed = urlparse(final_cluster_url)
hostname = parsed.hostname
if not hostname:
    hostname = url_raw.split("/")[0].split(":")[0]  # fallback

print(f"Hostname cần phân giải: {hostname}")

# Kiểm tra DNS
try:
    ip = socket.gethostbyname(hostname)
    print(f"✅ DNS phân giải thành công: {hostname} -> {ip}")
except socket.gaierror as e:
    print(f"❌ LỖI DNS: {e}")
    print("→ Hãy kiểm tra lại tên cluster (có thể cluster đã bị xóa hoặc sai tên)")
    print("→ Thử ping từ command line: ping", hostname)
    exit(1)

# Kết nối thử
print("\n🔌 Đang kết nối tới Weaviate Cloud...")
try:
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=final_cluster_url,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY.strip()),
    )
    print("✅ Kết nối thành công!")
except Exception as e:
    print(f"❌ Kết nối thất bại: {e}")
    exit(1)

# Truy vấn dữ liệu
try:
    collection = client.collections.get("Product")
    # Đếm số lượng
    try:
        agg = collection.aggregate.over_all(total_count=True)
        total = agg.total_count
    except AttributeError:
        res = client.query.aggregate("Product").with_meta_count().do()
        total = res["data"]["Aggregate"]["Product"][0]["meta"]["count"]
    print(f"\n📦 Tổng số sản phẩm: {total}")

    print("\n📌 CẤU TRÚC PROPERTIES (suy từ object mẫu):")
    sample = collection.query.fetch_objects(limit=1)
    if sample.objects:
        props = list(sample.objects[0].properties.keys())
        for p in props:
            print(f"  - {p}")
    else:
        print("  Không có object nào để lấy cấu trúc")

    # Lấy 3 object mẫu kèm vector
    print("\n📋 3 object mẫu (có vector):")
    response = collection.query.fetch_objects(limit=3, include_vector=True)
    for idx, obj in enumerate(response.objects):
        print(f"\n🔹 Object {idx+1}:")
        print(f"   UUID: {obj.uuid}")
        for k, v in obj.properties.items():
            if isinstance(v, str) and len(v) > 100:
                v = v[:100] + "..."
            print(f"   {k}: {v}")
        if obj.vector:
            print(f"   vector: độ dài {len(obj.vector)}, 5 số đầu: {obj.vector[:5]}")
        else:
            print("   vector: KHÔNG CÓ")
except Exception as e:
    print(f"❌ Lỗi truy vấn dữ liệu: {e}")
finally:
    client.close()
    print("\n🔒 Đã đóng kết nối.")