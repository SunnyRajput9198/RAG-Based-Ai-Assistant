# ═══════════════════════════════════════════════════════════════════════════════
# 📋 CHANGELOG - What's New in This File
# ═══════════════════════════════════════════════════════════════════════════════
# 🆕 ADDED: video_url tracking (for timestamp links)
# 🆕 ADDED: video_id extraction from YouTube
# 🆕 ADDED: video_number (unique ID per video)
# 🆕 ADDED: source_type field ('video')
# 🆕 ADDED: Optional progress_callback parameter
# 🆕 MODIFIED: Append to existing data instead of overwrite
# ═══════════════════════════════════════════════════════════════════════════════

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

def get_transcript(video_url, progress_callback=None):
    """
    Extract transcript from YouTube video
    
    Args:
        video_url: YouTube URL
        progress_callback: Optional function to report progress
        
    Returns:
        dict with title, chunks, video_url, video_id
        
    🆕 CHANGES:
    - Added progress_callback parameter
    - Returns video_url and video_id
    - Tracks progress during download and transcription
    """
    if progress_callback:
        progress_callback("📥 Downloading audio...")
        print("📥 Starting download...")
    
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
            video_id = info.get('id', '')  # 🆕 ADDED
            print(f"✅ Downloaded: {title}")
        
        if progress_callback:
            progress_callback("🎤 Transcribing audio (this may take a while)...")
            print("🎤 Starting transcription...")
        
        segments, _ = whisper_model.transcribe(f"{filename}.mp3")
        chunks = []
        
        # Count total segments first
        total_segments = sum(1 for _ in whisper_model.transcribe(f"{filename}.mp3")[0])
        
        # Re-transcribe with progress
        segments, _ = whisper_model.transcribe(f"{filename}.mp3")
        processed = 0
        
        for s in segments:
            chunks.append({
                "text": s.text.strip(), 
                "start": s.start, 
                "end": s.end
            })
            processed += 1
            
            # Report progress every 10 segments
            if progress_callback and processed % 10 == 0:
                progress = int((processed / max(total_segments, 1)) * 100)
                progress_callback(f"🎤 Transcribing... {progress}% complete")
                print(f"🎤 Progress: {progress}%")
        
        os.remove(f"{filename}.mp3")
        print(f"✅ Transcription complete: {len(chunks)} chunks")
        
        if progress_callback:
            progress_callback("✅ Transcription complete!")
        
        # 🆕 ADDED: Return video metadata
        return {
            "title": title, 
            "chunks": chunks,
            "video_url": video_url,  # 🆕 For timestamp links
            "video_id": video_id     # 🆕 YouTube video ID
        }
        
    except Exception as e:
        if progress_callback:
            progress_callback(f"❌ Error: {str(e)}")
        print(f"❌ Error in get_transcript: {e}")
        return None

def process_and_save(video_url, progress_callback=None):
    """
    Process YouTube video and save to database
    
    Args:
        video_url: YouTube URL
        progress_callback: Optional function to report progress
        
    Returns:
        dict with title and chunks count
        
    🆕 CHANGES:
    - Added progress_callback parameter
    - Saves video_url with each chunk
    - Generates consistent video_number for all chunks
    - Appends to existing data instead of overwriting
    - Adds source_type field ('video')
    """
    if progress_callback:
        progress_callback("🚀 Starting video processing...")
        print("🚀 Starting video processing...")
    
    data = get_transcript(video_url, progress_callback)
    
    if not data:
        if progress_callback:
            progress_callback("❌ Failed to extract transcript")
        print("❌ Failed to extract transcript")
        return None
    
    chunks = data['chunks']
    title = data['title']
    video_url_stored = data.get('video_url', '')  # 🆕 ADDED
    video_id = data.get('video_id', '')           # 🆕 ADDED
    
    # 🆕 ADDED: Generate unique number for this video
    video_number = str(uuid.uuid4())[:8]
    print(f"🆔 Generated video number: {video_number}")
    
    if progress_callback:
        progress_callback(f"🧮 Creating embeddings for {len(chunks)} chunks...")
        print(f"🧮 Creating {len(chunks)} embeddings...")
    
    texts = [c['text'] for c in chunks]
    embeddings = embedding_model.encode(texts).tolist()
    
    if progress_callback:
        progress_callback("💾 Saving to database...")
        print("💾 Saving to database...")
    
    # 🆕 MODIFIED: Add metadata to each chunk
    for i, chunk in enumerate(chunks):
        chunk['embedding'] = embeddings[i]
        chunk['title'] = title
        chunk['number'] = video_number      # 🆕 Same for all chunks
        chunk['video_url'] = video_url_stored  # 🆕 For timestamp links
        chunk['video_id'] = video_id           # 🆕 YouTube ID
        chunk['source_type'] = 'video'         # 🆕 Differentiate from PDFs
    
    # 🆕 MODIFIED: Append to existing data
    if os.path.exists("data.embeddings.joblib"):
        existing_df = joblib.load("data.embeddings.joblib")
        new_df = pd.DataFrame.from_records(chunks)
        df = pd.concat([existing_df, new_df], ignore_index=True)
        print(f"📊 Appended to existing data. Total: {len(df)} chunks")
    else:
        df = pd.DataFrame.from_records(chunks)
        print(f"📊 Created new database with {len(df)} chunks")
    
    joblib.dump(df, "data.embeddings.joblib")
    
    if progress_callback:
        progress_callback(f"✅ Successfully processed! {len(chunks)} chunks saved")
    
    print(f"✅ Saved! {len(chunks)} chunks")
    return {"title": title, "chunks": len(chunks)}

# ═══════════════════════════════════════════════════════════════════════════════
# 📋 COMPLETE CHANGELOG SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
# 🆕 ADDED: progress_callback parameter (optional)
# 🆕 ADDED: video_url tracking in chunks
# 🆕 ADDED: video_id extraction from YouTube
# 🆕 ADDED: video_number (unique per video, same for all chunks)
# 🆕 ADDED: source_type field ('video')
# 🆕 ADDED: Progress reporting at key stages
# 🆕 MODIFIED: Append to existing joblib instead of overwriting
# 🆕 ADDED: Detailed console logging
# ✅ BACKWARD COMPATIBLE: Works without progress_callback
# ═══════════════════════════════════════════════════════════════════════════════