import sys
import os
from pdf_processor import process_pdf_file, save_pdf_json
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=60)
COLLECTION_NAME = "edubot"

def process_and_save_pdf(pdf_path: str) -> dict:
    if not os.path.exists(pdf_path):
        return {"success": False, "error": "File not found"}

    filename = os.path.basename(pdf_path)
    print(f"Processing PDF: {filename}")

    result = process_pdf_file(pdf_path, filename)
    if not result:
        return {"success": False, "error": "Text extraction failed"}

    # Check if already processed
    existing = qdrant_client.scroll(
        collection_name=COLLECTION_NAME, limit=1,
        scroll_filter=models.Filter(must=[models.FieldCondition(key="number", match=models.MatchValue(value=result['pdf_id']))]),
        with_vectors=False
    )[0]
    if existing:
        return {"success": False, "error": "PDF already exists", "title": result['title']}

    save_pdf_json(result)

    print(f"Creating embeddings for {result['total_chunks']} chunks...")
    texts = [chunk['text'] for chunk in result['chunks']]
    embeddings = embedding_model.encode(texts, show_progress_bar=True).tolist()

    chunk_id = qdrant_client.count(COLLECTION_NAME).count

    points = []
    for i, chunk in enumerate(result['chunks']):
        points.append(models.PointStruct(
            id=chunk_id + i,
            vector=embeddings[i],
            payload={
                "title": result['title'],
                "number": result['pdf_id'],
                "text": chunk['text'],
                "source_type": "pdf",
                "page_estimate": chunk.get('page_estimate', 0),
                "start": None,
                "end": None,
                "video_url": None
            }
        ))

    BATCH_SIZE = 50
    for i in range(0, len(points), BATCH_SIZE):
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points[i:i+BATCH_SIZE])

    print(f"Saved {len(points)} chunks for: {result['title']}")
    return {"success": True, "title": result['title'], "pdf_id": result['pdf_id'], "chunks": result['total_chunks']}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_pdf.py <pdf_file_path>")
        sys.exit(1)
    result = process_and_save_pdf(sys.argv[1])
    print(result)