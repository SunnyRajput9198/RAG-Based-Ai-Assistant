import whisper
import json
import os
import yt_dlp
import uuid
import re

model = whisper.load_model("base")

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    if len(filename) > 100:
        filename = filename[:100]
    return filename

def transcribe_and_save(audio_path, number, title, video_url=None):
    result = model.transcribe(audio=audio_path, language="hi", task="translate", word_timestamps=False)
    chunks = []
    
    for segment in result["segments"]:
        chunk = {
            "number": number,
            "title": title,
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"]
        }
        
        # Add video URL for YouTube videos
        if video_url:
            chunk["video_url"] = video_url
            chunk["source_type"] = "video"
        
        chunks.append(chunk)
    
    chunks_with_metadata = {
        "chunks": chunks, 
        "text": result["text"],
        "video_url": video_url
    }
    
    safe_title = sanitize_filename(title)
    filepath = f"jsons/{number}_{safe_title}.json"
    
    with open(filepath, "w", encoding='utf-8') as f:
        json.dump(chunks_with_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved: {number}_{safe_title}.json ({len(chunks)} chunks)")

# Process local audios
audios = os.listdir("audios") if os.path.exists("audios") else []
for audio in audios:
    if "_" in audio:
        number = audio.split("_")[0]
        title = audio.split("_")[1][:-4]
        print(f"🎵 Processing: {number} - {title}")
        transcribe_and_save(f"audios/{audio}", number, title, video_url=None)

# Process YouTube URL
youtube_url = input("\n🎥 YouTube URL dalo (skip karne ke liye Enter): ").strip()
if youtube_url:
    filename = f"audio_{uuid.uuid4().hex}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'audios/{filename}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'quiet': True,
    }
    
    print("⬇️ Downloading audio...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        title = info.get('title', 'Unknown')
    
    existing_jsons = len([f for f in os.listdir("jsons") if f.endswith('.json')]) if os.path.exists("jsons") else 0
    number = str(existing_jsons + 1)
    
    print(f"🎤 Transcribing: {title}")
    transcribe_and_save(f"audios/{filename}.mp3", number, title, video_url=youtube_url)
    
    os.remove(f"audios/{filename}.mp3")
    print(f"🗑️ Cleaned up audio file")