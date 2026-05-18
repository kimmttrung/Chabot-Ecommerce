import os
import weaviate
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load các biến trong file .env
load_dotenv()

# Lấy các biến cấu hình ra
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# Khởi tạo mô hình nhúng Vector
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001", google_api_key=GOOGLE_API_KEY
)

# Khởi tạo kết nối Weaviate
weaviate_client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
)