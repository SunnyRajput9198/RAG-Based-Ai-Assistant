import yt_dlp
import uuid
import os
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

whisper_model = WhisperModel("base", device="cpu")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=60)
COLLECTION_NAME = "edubot"

def get_transcript(video_url, progress_callback=None):
    if progress_callback: progress_callback("Downloading audio...")
    filename = f"audio_{uuid.uuid4().hex}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{filename}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get('title', 'Unknown')
            video_id = info.get('id', '')

        if progress_callback: progress_callback("Transcribing audio...")
        segments, _ = whisper_model.transcribe(f"{filename}.mp3")
        chunks = [{"text": s.text.strip(), "start": s.start, "end": s.end} for s in segments]
        os.remove(f"{filename}.mp3")

        if progress_callback: progress_callback("Transcription complete!")
        return {"title": title, "chunks": chunks, "video_url": video_url, "video_id": video_id}

    except Exception as e:
        if progress_callback: progress_callback(f"Error: {str(e)}")
        print(f"Error: {e}")
        return None


def process_and_save(video_url, progress_callback=None):
    if progress_callback: progress_callback("Starting video processing...")

    data = get_transcript(video_url, progress_callback)
    if not data:
        return None

    chunks = data['chunks']
    title = data['title']
    video_number = str(uuid.uuid4())[:8]

    if progress_callback: progress_callback(f"Creating embeddings for {len(chunks)} chunks...")
    texts = [c['text'] for c in chunks]
    embeddings = embedding_model.encode(texts).tolist()

    if progress_callback: progress_callback("Saving to Qdrant...")

    # Existing chunk count for unique IDs
    chunk_id = qdrant_client.count(COLLECTION_NAME).count

    points = []
    for i, chunk in enumerate(chunks):
        points.append(models.PointStruct(
            id=chunk_id + i,
            vector=embeddings[i],
            payload={
                "title": title,
                "number": video_number,
                "start": chunk["start"],
                "end": chunk["end"],
                "text": chunk["text"],
                "video_url": data["video_url"],
                "video_id": data["video_id"],
                "source_type": "video"
            }
        ))

    # Batch upload
    BATCH_SIZE = 50
    for i in range(0, len(points), BATCH_SIZE):
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points[i:i+BATCH_SIZE])

    if progress_callback: progress_callback(f"Done! {len(chunks)} chunks saved")
    print(f"Saved {len(chunks)} chunks for: {title}")
    return {"title": title, "chunks": len(chunks)}