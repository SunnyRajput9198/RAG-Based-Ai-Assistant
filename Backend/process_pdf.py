"""
PDF ingestion pipeline.
Extracts text → builds parent-child chunks → embeds children → stores in Qdrant.
Parent chunks are stored with vectors=None and retrieved by parent_id lookup.
Registers the resource in the SQLite database.
"""

import sys
import os
from pdf_processor import process_pdf_file, save_pdf_json
from openai import OpenAI
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
from database import register_resource, init_db

load_dotenv()
init_db()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 500
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=60)
COLLECTION_NAME = "edubot"
COLLECTION_NAME_PARENTS = "edubot_parents"   # stores parent chunks (no vectors)


def _ensure_collections():
    """Create Qdrant collections if they don't exist."""
    if not qdrant_client.collection_exists(COLLECTION_NAME):
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )
    if not qdrant_client.collection_exists(COLLECTION_NAME_PARENTS):
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME_PARENTS,
            vectors_config=models.VectorParams(size=1, distance=models.Distance.COSINE),
        )


def get_embeddings(texts: list) -> list:
    """Embed texts in batches to stay within OpenAI's per-request input limit."""
    all_embeddings = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        response = openai_client.embeddings.create(input=batch, model=EMBEDDING_MODEL)
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


def process_and_save_pdf(pdf_path: str) -> dict:
    if not os.path.exists(pdf_path):
        return {"success": False, "error": "File not found"}

    filename = os.path.basename(pdf_path)

    result = process_pdf_file(pdf_path, filename)
    if not result:
        return {"success": False, "error": "Text extraction failed"}

    _ensure_collections()

    # Check if already processed
    existing, _ = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1,
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="number", match=models.MatchValue(value=result['pdf_id']))]
        ),
        with_vectors=False
    )
    if existing:
        return {"success": False, "error": "PDF already exists", "title": result['title']}

    save_pdf_json(result)

    children = result['children']
    parents = result['parents']

    # ── Embed child chunks ────────────────────────────────────────────────────
    print(f"🔢 Creating embeddings for {len(children)} child chunks...")
    child_texts = [c['text'] for c in children]
    child_embeddings = get_embeddings(child_texts)

    child_id_counter = qdrant_client.count(COLLECTION_NAME).count
    child_points = []
    for i, chunk in enumerate(children):
        child_points.append(models.PointStruct(
            id=child_id_counter + i,
            vector=child_embeddings[i],
            payload={
                "child_id": chunk["child_id"],
                "parent_id": chunk["parent_id"],
                "title": result['title'],
                "number": result['pdf_id'],
                "text": chunk['text'],
                "source_type": "pdf",
                "page_estimate": 0,
                "start": None,
                "end": None,
                "video_url": None,
            }
        ))

    # ── Store parent chunks (no vector needed — retrieved by parent_id) ───────
    parent_id_counter = qdrant_client.count(COLLECTION_NAME_PARENTS).count
    parent_points = []
    for i, parent in enumerate(parents):
        parent_points.append(models.PointStruct(
            id=parent_id_counter + i,
            vector=[0.0],   # placeholder — parents are fetched by ID, not searched
            payload={
                "parent_id": parent["parent_id"],
                "title": result['title'],
                "number": result['pdf_id'],
                "text": parent['text'],
                "source_type": "pdf",
                "page_estimate": 0,
                "start": None,
                "end": None,
                "video_url": None,
            }
        ))

    BATCH_SIZE = 50
    for i in range(0, len(child_points), BATCH_SIZE):
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=child_points[i:i + BATCH_SIZE])

    for i in range(0, len(parent_points), BATCH_SIZE):
        qdrant_client.upsert(collection_name=COLLECTION_NAME_PARENTS, points=parent_points[i:i + BATCH_SIZE])

    # Register in SQLite
    register_resource(
        resource_id=result['pdf_id'],
        title=result['title'],
        resource_type="pdf",
        chunk_count=len(children),
        file_size_bytes=result.get('file_size_bytes'),
    )

    print(f"✅ Saved {len(children)} child + {len(parents)} parent chunks for: {result['title']}")
    return {
        "success": True,
        "title": result['title'],
        "pdf_id": result['pdf_id'],
        "chunks": len(children),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_pdf.py <pdf_file_path>")
        sys.exit(1)
    r = process_and_save_pdf(sys.argv[1])
    print(r)
