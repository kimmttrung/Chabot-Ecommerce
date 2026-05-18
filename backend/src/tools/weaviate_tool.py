from crewai.tools import tool
from config.database import embeddings_model, weaviate_client


@tool("Tìm kiếm sản phẩm điện thoại và máy tính Phúc Anh")
def search_weaviate_tool(query: str) -> str:
    """Hàm này dùng để tìm kiếm sản phẩm dựa trên nhu cầu của khách hàng như cấu hình, tầm giá, tên máy."""
    # Biến câu query của user thành Vector
    query_vector = embeddings_model.embed_query(query)

    # Quét thực thể trên Weaviate
    result = (
        weaviate_client.query.get("Product", ["name", "price", "url", "specs"])
        .with_near_vector({"vector": query_vector})
        .with_limit(3)
        .do()
    )

    products = result["data"]["Get"]["Product"]
    if not products:
        return "Không tìm thấy sản phẩm nào phù hợp trong database."

    output = []
    for p in products:
        output.append(
            f"- {p['name']}\n  Giá: {p['price']} VND\n  Thông số: {p['specs']}\n  Link: {p['url']}"
        )
    return "\n\n".join(output)