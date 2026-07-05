"""
Reranking module using a cross-encoder model.
Retrieves a wider candidate set from Qdrant, rescores with a cross-encoder,
and returns the top-k most relevant chunks.

Uses BAAI/bge-reranker-base (runs on CPU, ~550MB).
Falls back gracefully to score-based ordering if the model is unavailable.
"""

from typing import List, Any

# Lazy-load the cross-encoder to avoid slow startup if not needed
_reranker = None
_reranker_loaded = False


def _load_reranker():
    global _reranker, _reranker_loaded
    if _reranker_loaded:
        return _reranker
    try:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("BAAI/bge-reranker-base", max_length=512)
        print("✅ Reranker loaded: BAAI/bge-reranker-base")
    except Exception as e:
        print(f"⚠️  Reranker unavailable ({e}). Falling back to vector similarity ordering.")
        _reranker = None
    _reranker_loaded = True
    return _reranker


def rerank(query: str, candidates: List[Any], top_k: int = 5) -> List[Any]:
    """
    Rerank Qdrant result candidates using a cross-encoder.

    Args:
        query: The user's search query.
        candidates: List of Qdrant ScoredPoint objects.
        top_k: Number of top results to return after reranking.

    Returns:
        Top-k reranked candidates (same type as input).
    """
    if not candidates:
        return candidates

    reranker = _load_reranker()

    if reranker is None:
        # Fallback: just return top_k by vector score
        return sorted(candidates, key=lambda r: r.score, reverse=True)[:top_k]

    # Build (query, passage) pairs for the cross-encoder
    pairs = [(query, r.payload.get("text", "")) for r in candidates]

    try:
        scores = reranker.predict(pairs)
        # Zip scores with candidates and sort descending
        scored = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]
    except Exception as e:
        print(f"Reranker inference error: {e}. Falling back to vector scores.")
        return sorted(candidates, key=lambda r: r.score, reverse=True)[:top_k]
