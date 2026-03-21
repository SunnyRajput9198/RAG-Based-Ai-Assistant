import os
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

load_dotenv()

# Client mein timeout badhao
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)
COLLECTION_NAME = "edubot"

if not qdrant_client.collection_exists(COLLECTION_NAME):
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )
    print("✅ Collection created")

model = SentenceTransformer('all-MiniLM-L6-v2')

# Existing titles aur chunk_id Qdrant se fetch karo
existing = qdrant_client.scroll(collection_name=COLLECTION_NAME, limit=10000, with_payload=["title"], with_vectors=False)[0]
existing_titles = list(set(p.payload["title"] for p in existing))
chunk_id = qdrant_client.count(COLLECTION_NAME).count
print(f"📊 Existing: {chunk_id} chunks from {len(existing_titles)} videos/PDFs")

jsons = [f for f in os.listdir("jsons") if f.endswith('.json')]
if not jsons:
    print("⚠️ No JSON files found!")
    exit()

processed_count = 0

for json_file in jsons:
    try:
        with open(f"jsons/{json_file}", 'r', encoding='utf-8', errors='ignore') as f:
            content = json.load(f)
    except Exception as e:
        print(f"❌ Failed: {json_file} — {e}")
        continue

    if 'chunks' not in content or not content['chunks']:
        continue

    title = content['chunks'][0].get('title', 'Unknown')
    if title in existing_titles:
        print(f"⏭️ Skipping {json_file}")
        continue

    valid_chunks = [c for c in content['chunks'] if c.get('text', '').strip()]
    if not valid_chunks:
        continue

    print(f"🔄 Embedding: {json_file}")
    embeddings = model.encode([c['text'] for c in valid_chunks]).tolist()
    video_url = content.get('video_url', None)

    points = []
    for i, chunk in enumerate(valid_chunks):
        points.append(models.PointStruct(
            id=chunk_id,
            vector=embeddings[i],
            payload={
                "number": chunk.get("number"),
                "title": chunk.get("title"),
                "start": chunk.get("start"),
                "end": chunk.get("end"),
                "text": chunk.get("text"),
                "video_url": chunk.get("video_url") or video_url,
                "source_type": "pdf" if "page_estimate" in chunk else "video",
            }
        ))
        chunk_id += 1

    # Ek saath sab mat bhejo — 50-50 ke batches mein
BATCH_SIZE = 50
for i in range(0, len(points), BATCH_SIZE):
    batch = points[i:i+BATCH_SIZE]
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=batch)
    print(f"  Uploaded {min(i+BATCH_SIZE, len(points))}/{len(points)} points")
    processed_count += 1
    print(f"✅ {len(valid_chunks)} chunks saved — {title}")

print(f"\n✅ Done! {processed_count} new files processed. Total: {chunk_id} chunks")