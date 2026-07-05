"""
Semantic chunking module.
Implements sentence-boundary + parent-child chunking strategy.

- Child chunks (100-200 chars): stored in Qdrant for precise semantic search.
- Parent chunks (1000-1500 chars): retrieved when a child matches, fed to LLM for full context.

Uses nltk for sentence tokenization. Falls back to period-splitting if nltk is unavailable.
"""

import uuid
import re
from typing import List, Dict, Tuple, Optional

# Try to use nltk for sentence tokenization
try:
    import nltk
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)
    from nltk.tokenize import sent_tokenize as _nltk_sent_tokenize
    _USE_NLTK = True
except ImportError:
    _USE_NLTK = False
    _nltk_sent_tokenize = None  # type: ignore


def _sentence_split(text: str) -> List[str]:
    """Split text into sentences using nltk or simple fallback."""
    if _USE_NLTK and _nltk_sent_tokenize is not None:
        return _nltk_sent_tokenize(text)
    # Fallback: split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def build_parent_child_chunks(
    text: str,
    source_id: str,
    title: str,
    source_type: str,
    child_size: int = 150,
    parent_size: int = 1200,
    overlap_sentences: int = 1,
    extra_payload: Optional[Dict] = None,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Split text into parent and child chunks.

    Args:
        text: Full document/transcript text.
        source_id: Unique ID for the source (pdf_id or video_number).
        title: Title of the source.
        source_type: 'pdf' or 'video'.
        child_size: Target character length for child chunks (for embedding).
        parent_size: Target character length for parent chunks (for LLM context).
        overlap_sentences: How many sentences from the previous group to carry over.
        extra_payload: Additional fields to attach (e.g. video_url, video_id, start, end).

    Returns:
        (parent_chunks, child_chunks)
        Each chunk is a dict ready to insert into Qdrant.
        Child chunks include a 'parent_id' field linking to their parent.
    """
    sentences = _sentence_split(text)
    if not sentences:
        return [], []

    extra = extra_payload or {}

    # ── Build parent chunks ──────────────────────────────────────────────────
    parents: List[Dict] = []
    current_sentences: List[str] = []
    current_len = 0

    def _flush_parent(sents: List[str]) -> Dict:
        parent_text = " ".join(sents)
        return {
            "parent_id": str(uuid.uuid4()),
            "text": parent_text,
            "number": source_id,
            "title": title,
            "source_type": source_type,
            **extra,
        }

    for i, sent in enumerate(sentences):
        current_sentences.append(sent)
        current_len += len(sent)

        if current_len >= parent_size:
            parents.append(_flush_parent(current_sentences))
            # Carry over last N sentences for overlap
            current_sentences = current_sentences[-overlap_sentences:] if overlap_sentences > 0 else []
            current_len = sum(len(s) for s in current_sentences)

    # Flush remaining
    if current_sentences:
        parents.append(_flush_parent(current_sentences))

    # ── Build child chunks from each parent ──────────────────────────────────
    children: List[Dict] = []

    for parent in parents:
        p_text = parent["text"]
        p_sents = _sentence_split(p_text)
        child_sents: List[str] = []
        child_len = 0

        for sent in p_sents:
            child_sents.append(sent)
            child_len += len(sent)

            if child_len >= child_size:
                child_text = " ".join(child_sents)
                children.append({
                    "child_id": str(uuid.uuid4()),
                    "parent_id": parent["parent_id"],
                    "text": child_text,
                    "number": source_id,
                    "title": title,
                    "source_type": source_type,
                    **extra,
                })
                child_sents = []
                child_len = 0

        # Flush remaining child sentences
        if child_sents:
            child_text = " ".join(child_sents)
            if child_text.strip():
                children.append({
                    "child_id": str(uuid.uuid4()),
                    "parent_id": parent["parent_id"],
                    "text": child_text,
                    "number": source_id,
                    "title": title,
                    "source_type": source_type,
                    **extra,
                })

    return parents, children


def chunk_transcript_segments(
    segments: List[Dict],
    source_id: str,
    title: str,
    video_url: str,
    video_id: str,
    parent_size: int = 1200,
    child_size: int = 150,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Build parent-child chunks from Whisper transcript segments.
    Groups segments into parent windows, preserving start/end timestamps.

    Returns:
        (parent_chunks, child_chunks)
    """
    if not segments:
        return [], []

    parents: List[Dict] = []
    children: List[Dict] = []

    current_segs: List[Dict] = []
    current_len = 0

    def _flush(segs: List[Dict]):
        combined_text = " ".join(s["text"] for s in segs)
        parent_id = str(uuid.uuid4())
        parent = {
            "parent_id": parent_id,
            "text": combined_text,
            "number": source_id,
            "title": title,
            "source_type": "video",
            "start": segs[0]["start"],
            "end": segs[-1]["end"],
            "video_url": video_url,
            "video_id": video_id,
        }
        parents.append(parent)

        # Build children from this parent
        child_text = ""
        child_start = segs[0]["start"]
        child_end = segs[0]["end"]

        for seg in segs:
            if len(child_text) + len(seg["text"]) >= child_size and child_text:
                children.append({
                    "child_id": str(uuid.uuid4()),
                    "parent_id": parent_id,
                    "text": child_text.strip(),
                    "number": source_id,
                    "title": title,
                    "source_type": "video",
                    "start": child_start,
                    "end": child_end,
                    "video_url": video_url,
                    "video_id": video_id,
                })
                child_text = seg["text"]
                child_start = seg["start"]
                child_end = seg["end"]
            else:
                child_text += " " + seg["text"]
                child_end = seg["end"]

        if child_text.strip():
            children.append({
                "child_id": str(uuid.uuid4()),
                "parent_id": parent_id,
                "text": child_text.strip(),
                "number": source_id,
                "title": title,
                "source_type": "video",
                "start": child_start,
                "end": child_end,
                "video_url": video_url,
                "video_id": video_id,
            })

    for seg in segments:
        current_segs.append(seg)
        current_len += len(seg["text"])

        if current_len >= parent_size:
            _flush(current_segs)
            current_segs = []
            current_len = 0

    if current_segs:
        _flush(current_segs)

    return parents, children
