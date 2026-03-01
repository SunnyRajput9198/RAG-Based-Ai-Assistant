import whisper
import json
import os
import yt_dlp
import uuid

model = whisper.load_model("base")

def transcribe_and_save(audio_path, number, title):
    result = model.transcribe(audio=audio_path, language="hi", task="translate", word_timestamps=False)
    chunks = []
    for segment in result["segments"]:
        chunks.append({
            "number": number,      # "1", "2", "3"
            "title": title,        # actual YouTube title
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"]
        })
    chunks_with_metadata = {"chunks": chunks, "text": result["text"]}
    with open(f"jsons/{number}_{title}.json", "w") as f:
        json.dump(chunks_with_metadata, f)
    print(f"Saved: {number}_{title}.json")

# Local audios
audios = os.listdir("audios")
for audio in audios:
    if "_" in audio:
        number = audio.split("_")[0]
        title = audio.split("_")[1][:-4]
        print(number, title)
        transcribe_and_save(f"audios/{audio}", number, title)

# YouTube URL
youtube_url = input("\nYouTube URL dalo (skip karne ke liye Enter): ").strip()
if youtube_url:
    filename = f"audio_{uuid.uuid4().hex}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'audios/{filename}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        title = info.get('title', 'Unknown')
    
    number = str(len(os.listdir("jsons")) + 1)
    transcribe_and_save(f"audios/{filename}.mp3", number, title)
    os.remove(f"audios/{filename}.mp3")