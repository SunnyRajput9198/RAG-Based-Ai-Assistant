"""
Shared audio transcription utility.
Handles OpenAI Whisper API 25MB limit by splitting large files into chunks,
transcribing each part, and merging segments with corrected timestamps.
"""

import os
import math
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key or _api_key.startswith("your-"):
    import warnings
    warnings.warn("OPENAI_API_KEY is not set or is a placeholder. Transcription will fail.", RuntimeWarning)
    _api_key = "placeholder"   # allows import to succeed; real calls will fail with auth error

openai_client = OpenAI(api_key=_api_key)

MAX_FILE_SIZE_MB = 24          # Stay safely under the 25MB API limit
SPLIT_DURATION_MINS = 20       # Each split chunk = 20 minutes of audio


def _get_file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def _transcribe_single(audio_path: str, time_offset: float = 0.0) -> dict:
    """
    Send a single audio file to OpenAI Whisper API.
    Applies time_offset to all segment timestamps so they reflect
    position in the original full audio.

    Returns: {"segments": [...], "text": "..."}
    """
    with open(audio_path, "rb") as f:
        response = openai_client.audio.transcriptions.create(
            file=f,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

    segments = [
        {
            "start": round(s.start + time_offset, 2),
            "end":   round(s.end   + time_offset, 2),
            "text":  s.text.strip()
        }
        for s in (response.segments or [])
    ]

    return {"segments": segments, "text": response.text or ""}


def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe an audio file using OpenAI Whisper API.
    Automatically splits files larger than 24MB into 20-minute parts,
    transcribes each, and merges results with corrected timestamps.

    Args:
        audio_path: Path to the MP3/audio file.

    Returns:
        {
            "segments": [{"start": float, "end": float, "text": str}, ...],
            "text": str   # full concatenated transcript
        }
    """
    size_mb = _get_file_size_mb(audio_path)
    print(f"🎵 Audio file size: {size_mb:.1f} MB")

    if size_mb <= MAX_FILE_SIZE_MB:
        # Small enough — send directly
        print("📤 Sending to Whisper API...")
        return _transcribe_single(audio_path, time_offset=0.0)

    # File too large — split using pydub
    print(f"✂️  File exceeds {MAX_FILE_SIZE_MB}MB, splitting into {SPLIT_DURATION_MINS}-min parts...")

    try:
        from pydub import AudioSegment
    except ImportError:
        raise RuntimeError(
            "pydub is required for splitting large audio files. "
            "Install it with: pip install pydub"
        )

    audio = AudioSegment.from_mp3(audio_path)
    total_duration_ms = len(audio)
    split_duration_ms = SPLIT_DURATION_MINS * 60 * 1000

    num_parts = math.ceil(total_duration_ms / split_duration_ms)
    print(f"📂 Splitting into {num_parts} parts...")

    all_segments = []
    full_text_parts = []
    temp_files = []

    try:
        for part_idx in range(num_parts):
            start_ms = part_idx * split_duration_ms
            end_ms   = min(start_ms + split_duration_ms, total_duration_ms)
            time_offset_secs = start_ms / 1000.0

            part_audio = audio[start_ms:end_ms]

            # Write part to a temp file
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            part_audio.export(tmp.name, format="mp3")
            tmp.close()
            temp_files.append(tmp.name)

            part_size_mb = _get_file_size_mb(tmp.name)
            print(f"  Part {part_idx + 1}/{num_parts} — {part_size_mb:.1f} MB, offset {time_offset_secs:.0f}s")

            result = _transcribe_single(tmp.name, time_offset=time_offset_secs)
            all_segments.extend(result["segments"])
            full_text_parts.append(result["text"])

    finally:
        # Always clean up temp files
        for tmp_path in temp_files:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    print(f"✅ Transcription complete — {len(all_segments)} segments total")
    return {
        "segments": all_segments,
        "text": " ".join(full_text_parts)
    }
