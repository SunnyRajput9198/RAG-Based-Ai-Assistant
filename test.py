import yt_dlp
import json
import os
import uuid
from faster_whisper import WhisperModel
filename = f"audio_{uuid.uuid4().hex}"
model = WhisperModel("base", device="cpu")
def parse_captions(raw):
    data = json.loads(raw)
    chunks = []
    for event in data.get("events", []):
        for seg in event.get("segs", []):
            utf8 = seg.get("utf8", "")
            if utf8 and utf8 != "\n":
                chunks.append({
                    "text": utf8.strip(),
                    "start": event.get("tStartMs", 0) / 1000,
                    "end": (event.get("tStartMs", 0) + event.get("dDurationMs", 0)) / 1000
                })
    return chunks
def get_transcript(video_url):
    # Audio download
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{filename}.%(ext)s',
        'js_runtimes': 'nodejs',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        title = info.get('title', 'Unknown')

    # Transcribe
    segments, _ = model.transcribe(f"{filename}.mp3")
    chunks = [{"text": s.text.strip(), "start": s.start, "end": s.end} for s in segments]
    print(f"Title: {title}, Chunks: {len(chunks)}")
    return {"title": title, "chunks": chunks}

get_transcript("https://youtu.be/YyepU5ztLf4?si=H2tU6A4xc9Y8duDE")
