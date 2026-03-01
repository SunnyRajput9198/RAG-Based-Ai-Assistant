import yt_dlp
import uuid
import os
import json
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer
import joblib
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

whisper_model = WhisperModel("base", device="cpu")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_transcript(video_url):
    filename = f"audio_{uuid.uuid4().hex}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{filename}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        title = info.get('title', 'Unknown')

    segments, _ = whisper_model.transcribe(f"{filename}.mp3")
    chunks = [{"text": s.text.strip(), "start": s.start, "end": s.end} for s in segments]
    os.remove(f"{filename}.mp3")
    return {"title": title, "chunks": chunks}

def process_and_save(video_url):
    data = get_transcript(video_url)
    if not data:
        return None
    chunks = data['chunks']
    title = data['title']
    texts = [c['text'] for c in chunks]
    embeddings = embedding_model.encode(texts).tolist()
    for i, chunk in enumerate(chunks):
        chunk['embedding'] = embeddings[i]
        chunk['title'] = title
    df = pd.DataFrame.from_records(chunks)
    joblib.dump(df, "data.embeddings.joblib")
    print(f"Saved! {len(chunks)} chunks")
    return {"title": title, "chunks": len(chunks)}