"""
YouTube video ingestion pipeline.
Downloads audio → transcribes → builds parent-child chunks → embeds → stores in Qdrant.
Registers the resource in the SQLite database.
"""

import yt_dlp
import uuid
import os
from typing import Any
from openai import OpenAI
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
from audio_utils import transcribe_audio
from chunker import chunk_transcript_segments
from database import register_resource, init_db

load_dotenv()
init_db()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 500
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=60)
COLLECTION_NAME = "edubot"
COLLECTION_NAME_PARENTS = "edubot_parents"


def _ensure_collections():
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
    all_embeddings = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        response = openai_client.embeddings.create(input=batch, model=EMBEDDING_MODEL)
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


def _video_already_exists(video_id: str) -> bool:
    existing, _ = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1,
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="video_id", match=models.MatchValue(value=video_id))]
        ),
        with_vectors=False
    )
    return len(existing) > 0


def get_transcript(video_url, progress_callback=None):
    if progress_callback: progress_callback("Downloading audio...")
    filename = f"audio_{uuid.uuid4().hex}"
    ydl_opts = {  # type: ignore[var-annotated]
        'format': 'bestaudio/best',
        'outtmpl': f'{filename}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            info = ydl.extract_info(video_url, download=True)
            title: str = str((info or {}).get('title', 'Unknown') or 'Unknown')
            video_id: str = str((info or {}).get('id', '') or '')

        if progress_callback: progress_callback("Transcribing audio...")
        result = transcribe_audio(f"{filename}.mp3")
        segments = result["segments"]
        os.remove(f"{filename}.mp3")

        if progress_callback: progress_callback("Transcription complete!")
        return {"title": title, "segments": segments, "video_url": video_url, "video_id": video_id}

    except Exception as e:
        if os.path.exists(f"{filename}.mp3"):
            os.remove(f"{filename}.mp3")
        if progress_callback: progress_callback(f"Error: {str(e)}")
        print(f"Error: {e}")
        return None


def process_and_save(video_url, progress_callback=None):
    if progress_callback: progress_callback("Starting video processing...")

    # Check for duplicate BEFORE downloading
    if progress_callback: progress_callback("Checking for duplicates...")
    try:
        check_opts = {'quiet': True}  # type: ignore[var-annotated]
        with yt_dlp.YoutubeDL(check_opts) as ydl:  # type: ignore[arg-type]
            info = ydl.extract_info(video_url, download=False)
            video_id_check: str = str((info or {}).get('id', '') or '')
            title_check: str = str((info or {}).get('title', 'Unknown') or 'Unknown')
    except Exception as e:
        if progress_callback: progress_callback(f"Error: {str(e)}")
        return None

    if video_id_check and _video_already_exists(video_id_check):
        print(f"⏭️ Already exists: {title_check}")
        if progress_callback: progress_callback("Video already processed, skipping.")
        return {"title": title_check, "chunks": 0, "already_exists": True}

    data = get_transcript(video_url, progress_callback)
    if not data:
        return None

    _ensure_collections()

    video_number = str(uuid.uuid4())[:8]
    segments = data['segments']
    title = data['title']

    if progress_callback: progress_callback("Building semantic chunks...")
    parents, children = chunk_transcript_segments(
        segments=segments,
        source_id=video_number,
        title=title,
        video_url=data['video_url'],
        video_id=data['video_id'],
        parent_size=1200,
        child_size=150,
    )
    print(f"  → {len(parents)} parent chunks, {len(children)} child chunks")

    if progress_callback: progress_callback(f"Creating embeddings for {len(children)} child chunks...")
    child_texts = [c['text'] for c in children]
    child_embeddings = get_embeddings(child_texts)

    if progress_callback: progress_callback("Saving to Qdrant...")
    child_id_counter = qdrant_client.count(COLLECTION_NAME).count

    child_points = []
    for i, chunk in enumerate(children):
        child_points.append(models.PointStruct(
            id=child_id_counter + i,
            vector=child_embeddings[i],
            payload={
                "child_id": chunk["child_id"],
                "parent_id": chunk["parent_id"],
                "title": title,
                "number": video_number,
                "start": chunk.get("start"),
                "end": chunk.get("end"),
                "text": chunk["text"],
                "video_url": data["video_url"],
                "video_id": data["video_id"],
                "source_type": "video",
            }
        ))

    parent_id_counter = qdrant_client.count(COLLECTION_NAME_PARENTS).count
    parent_points = []
    for i, parent in enumerate(parents):
        parent_points.append(models.PointStruct(
            id=parent_id_counter + i,
            vector=[0.0],
            payload={
                "parent_id": parent["parent_id"],
                "title": title,
                "number": video_number,
                "start": parent.get("start"),
                "end": parent.get("end"),
                "text": parent["text"],
                "video_url": data["video_url"],
                "video_id": data["video_id"],
                "source_type": "video",
            }
        ))

    BATCH_SIZE = 50
    for i in range(0, len(child_points), BATCH_SIZE):
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=child_points[i:i + BATCH_SIZE])
    for i in range(0, len(parent_points), BATCH_SIZE):
        qdrant_client.upsert(collection_name=COLLECTION_NAME_PARENTS, points=parent_points[i:i + BATCH_SIZE])

    # Register in SQLite
    register_resource(
        resource_id=video_number,
        title=title,
        resource_type="video",
        chunk_count=len(children),
        video_url=data['video_url'],
        video_id=data['video_id'],
    )

    if progress_callback: progress_callback(f"Done! {len(children)} chunks saved")
    print(f"✅ Saved {len(children)} child + {len(parents)} parent chunks for: {title}")
    return {"title": title, "chunks": len(children)}
