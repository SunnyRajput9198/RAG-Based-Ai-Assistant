from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from pydantic import BaseModel
from openai import OpenAI
import os, json, asyncio, uuid, concurrent.futures, functools
from dotenv import load_dotenv
from process_youtube import process_and_save
from process_pdf import process_and_save_pdf
from qdrant_client import QdrantClient, models
from typing import Optional, cast, List
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from reranker import rerank
from database import (
    init_db,
    get_or_create_session,
    clear_session_messages,
    save_message,
    get_recent_messages,
    get_all_resources,
    delete_resource,
)

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()
init_db()

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# ── Clients ───────────────────────────────────────────────────────────────────
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=60
)
COLLECTION_NAME = "edubot"
COLLECTION_NAME_PARENTS = "edubot_parents"

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-5-mini"

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
MAX_UPLOAD_MB = 50

# ── App + middleware ──────────────────────────────────────────────────────────
app = FastAPI()
app.state.limiter = limiter

# Wrap the slowapi handler to match FastAPI's ExceptionHandler signature
async def _rate_limit_handler(request: Request, exc: Exception) -> Response:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please slow down."})

app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# Secure CORS — read allowed origins from env, default to localhost only
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def get_embedding(text: str) -> list:
    response = openai_client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
    return response.data[0].embedding


def _fetch_parent_text(parent_id: str) -> str:
    try:
        results, _ = qdrant_client.scroll(
            collection_name=COLLECTION_NAME_PARENTS,
            limit=1,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="parent_id", match=models.MatchValue(value=parent_id)
                    )
                ]
            ),
            with_vectors=False,
            with_payload=True,
        )
        if results:
            return (results[0].payload or {}).get("text", "")
    except Exception:
        pass
    return ""


def _query_qdrant(embedding: list, video_id: Optional[str], limit: int = 20) -> list:
    return qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=limit,
        query_filter=(
            models.Filter(
                must=[
                    models.FieldCondition(
                        key="number", match=models.MatchValue(value=video_id)
                    )
                ]
            )
            if video_id
            else None
        ),
    ).points


def _scroll_all(source_type_filter: Optional[str] = None) -> list:
    """Paginate all Qdrant points — used as fallback if DB is empty."""
    # Collection may not exist yet if no content has been ingested
    try:
        if not qdrant_client.collection_exists(COLLECTION_NAME):
            return []
    except Exception:
        return []

    seen = {}
    offset = None
    while True:
        try:
            batch, next_offset = qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
        except Exception:
            break
        for r in batch:
            p = r.payload or {}
            num = p.get("number")
            if num in seen:
                continue
            if source_type_filter == "pdf" and p.get("source_type") != "pdf":
                continue
            if source_type_filter == "video" and p.get("source_type") == "pdf":
                continue
            seen[num] = {
                "id": str(num),
                "title": p.get("title"),
                "type": source_type_filter or p.get("source_type", "video"),
            }
        if next_offset is None:
            break
        offset = next_offset
    return list(seen.values())


def _suggested_questions(query_message: str, assistant_reply: str) -> list:
    try:
        prompt = (
            f'Based on: Q: "{query_message}" A: "{assistant_reply[:300]}"\n'
            f"Generate 3 follow-up questions, one per line, no numbering."
        )
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[cast(ChatCompletionMessageParam, {"role": "user", "content": prompt})],
            temperature=0.7,
        )
        lines = (response.choices[0].message.content or "").strip().split("\n")
        return [
            q.strip().lstrip("*-. 123456789")
            for q in lines
            if q.strip() and len(q.strip()) > 10
        ][:3]
    except Exception as e:
        print(f"Suggested questions error: {e}")
        return []


# ── Models ────────────────────────────────────────────────────────────────────


class Query(BaseModel):
    message: str
    VideoId: Optional[str] = None
    session_id: Optional[str] = None


class VideoRequest(BaseModel):
    url: str


# ── Streaming chat ────────────────────────────────────────────────────────────


@app.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, query: Query):
    """
    SSE streaming chat endpoint.
    - Tokens stream to the client as they arrive.
    - On client disconnect, the OpenAI generator is cancelled immediately.
    - DB writes are protected by try/except so a write failure never hangs the stream.
    """
    loop = asyncio.get_running_loop()

    session_id = query.session_id or str(uuid.uuid4())
    get_or_create_session(session_id)

    embedding = await loop.run_in_executor(_executor, get_embedding, query.message)
    candidates = await loop.run_in_executor(
        _executor, _query_qdrant, embedding, query.VideoId, 20
    )

    if not candidates:

        async def _empty():
            yield f"data: {json.dumps({'type': 'error', 'content': 'No relevant content found.'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'sources': [], 'suggested_questions': []})}\n\n"

        return StreamingResponse(_empty(), media_type="text/event-stream")

    reranked = await loop.run_in_executor(
        _executor, rerank, query.message, candidates, 5
    )

    # Fetch parent context for each matched child chunk
    context_chunks = []
    for r in reranked:
        p = r.payload or {}
        parent_id = p.get("parent_id")
        parent_text = ""
        if parent_id:
            parent_text = await loop.run_in_executor(
                _executor, _fetch_parent_text, parent_id
            )
        context_chunks.append(
            {
                "title": p.get("title"),
                "number": p.get("number"),
                "start": p.get("start"),
                "end": p.get("end"),
                "text": parent_text or p.get("text"),
            }
        )

    chunks_json = json.dumps(context_chunks)
    history = get_recent_messages(session_id, limit=6)

    system_prompt = f"""You are EduBot, an AI teaching assistant for the Sigma Web Development course.

Use ONLY the following video/document chunks to answer the question:
{chunks_json}

Instructions:
- Answer clearly and in detail based on the context above
- If this question relates to previous conversation, acknowledge and build upon it
- Mention the video/document title and timestamp where relevant
- If answer not in context, say "I don't have information about this in the current videos/documents"
- Use simple language, explain like a teacher"""

    messages: List[ChatCompletionMessageParam] = [
        cast(ChatCompletionMessageParam, {"role": "system", "content": system_prompt})
    ]
    for msg in history:
        messages.append(cast(ChatCompletionMessageParam, {"role": msg.role, "content": msg.content}))
    messages.append(cast(ChatCompletionMessageParam, {"role": "user", "content": query.message}))

    # Build sources metadata (from child chunk payloads)
    sources = []
    for r in reranked:
        p = r.payload or {}
        start_seconds = int(p.get("start") or 0)
        if p.get("source_type") == "pdf":
            sources.append(
                {
                    "videoId": str(p.get("number")),
                    "videoTitle": p.get("title"),
                    "timestamp": f"Page ~{p.get('page_estimate', 0)}",
                    "similarity": round(r.score, 3),
                    "text_preview": str(p.get("text", ""))[:150] + "...",
                    "source_type": "pdf",
                    "video_url": None,
                }
            )
        else:
            sources.append(
                {
                    "videoId": str(p.get("number")),
                    "videoTitle": p.get("title"),
                    "timestamp": f"{start_seconds // 60}:{start_seconds % 60:02d}",
                    "timestamp_seconds": start_seconds,
                    "similarity": round(r.score, 3),
                    "text_preview": str(p.get("text", ""))[:150] + "...",
                    "source_type": "video",
                    "video_url": p.get("video_url"),
                }
            )

    # Use an asyncio Event to detect client disconnect
    disconnect_event = asyncio.Event()

    async def _detect_disconnect():
        await request.is_disconnected()
        disconnect_event.set()

    asyncio.ensure_future(_detect_disconnect())

    async def _stream():
        full_reply = ""

        # Bridge the blocking OpenAI iterator (running in an executor thread)
        # with this async generator via a queue.
        # This avoids iterating a sync iterator directly inside async code.
        queue: asyncio.Queue = asyncio.Queue()

        def _run_openai_stream():
            """Runs entirely in an executor thread — pushes tokens into queue."""
            try:
                from openai import Stream
                openai_stream = cast(
                    Stream[ChatCompletionChunk],
                    openai_client.chat.completions.create(
                        model=CHAT_MODEL,#type: ignore
                        messages=messages,#type: ignore
                        temperature=0.7,
                        stream=True,
                    ),
                )
                for chunk in openai_stream:
                    if disconnect_event.is_set():
                        try:
                            openai_stream.close()
                        except Exception:
                            pass
                        loop.call_soon_threadsafe(queue.put_nowait, None)
                        return
                    delta = chunk.choices[0].delta.content
                    if delta:
                        loop.call_soon_threadsafe(queue.put_nowait, delta)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, f"__ERROR__{exc}")
                return
            loop.call_soon_threadsafe(queue.put_nowait, None)  # normal sentinel

        loop.run_in_executor(_executor, _run_openai_stream)

        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, str) and item.startswith("__ERROR__"):
                    yield f"data: {json.dumps({'type': 'error', 'content': item[len('__ERROR__'):]})}\n\n"
                    return
                full_reply += item
                yield f"data: {json.dumps({'type': 'token', 'content': item})}\n\n"
        except GeneratorExit:
            disconnect_event.set()
            return

        # ── Post-stream: persist to DB ────────────────────────────────────────
        try:
            save_message(session_id, "user", query.message)
            save_message(
                session_id, "assistant", full_reply, sources_json=json.dumps(sources)
            )
        except Exception as e:
            # Non-fatal — log but don't fail the response
            print(f"[db] Failed to save messages for session {session_id}: {e}")

        # ── Generate suggested questions (non-blocking) ───────────────────────
        try:
            suggested = await loop.run_in_executor(
                _executor,
                functools.partial(_suggested_questions, query.message, full_reply),
            )
        except Exception:
            suggested = []

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'sources': sources, 'suggested_questions': suggested})}\n\n"

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering for SSE
        },
    )


# ── Non-streaming chat ────────────────────────────────────────────────────────


@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, query: Query):
    loop = asyncio.get_running_loop()
    session_id = query.session_id or str(uuid.uuid4())
    get_or_create_session(session_id)

    embedding = await loop.run_in_executor(_executor, get_embedding, query.message)
    candidates = await loop.run_in_executor(
        _executor, _query_qdrant, embedding, query.VideoId, 20
    )

    if not candidates:
        return {"content": "No content found.", "sources": [], "session_id": session_id}

    reranked = await loop.run_in_executor(
        _executor, rerank, query.message, candidates, 5
    )

    context_chunks = []
    for r in reranked:
        p = r.payload or {}
        parent_id = p.get("parent_id")
        parent_text = ""
        if parent_id:
            parent_text = await loop.run_in_executor(
                _executor, _fetch_parent_text, parent_id
            )
        context_chunks.append(
            {
                "title": p.get("title"),
                "number": p.get("number"),
                "start": p.get("start"),
                "end": p.get("end"),
                "text": parent_text or p.get("text"),
            }
        )

    chunks_json = json.dumps(context_chunks)
    history = get_recent_messages(session_id, limit=6)
    system_prompt = f"""You are EduBot, an AI teaching assistant for the Sigma Web Development course.

Use ONLY the following video/document chunks to answer the question:
{chunks_json}

Instructions:
- Answer clearly and in detail based on the context above
- Mention the video/document title and timestamp where relevant
- If answer not in context, say "I don't have information about this in the current videos/documents"
- Use simple language, explain like a teacher"""

    messages: List[ChatCompletionMessageParam] = [
        cast(ChatCompletionMessageParam, {"role": "system", "content": system_prompt})
    ]
    for msg in history:
        messages.append(cast(ChatCompletionMessageParam, {"role": msg.role, "content": msg.content}))
    messages.append(cast(ChatCompletionMessageParam, {"role": "user", "content": query.message}))

    def _complete() -> str:
        return (
            openai_client.chat.completions.create(
                model=CHAT_MODEL, messages=messages, temperature=0.7
            )
            .choices[0]
            .message.content
            or ""
        )

    assistant_reply = await loop.run_in_executor(_executor, _complete)

    try:
        save_message(session_id, "user", query.message)
        save_message(session_id, "assistant", assistant_reply)
    except Exception as e:
        print(f"[db] save_message failed: {e}")

    sources = []
    for r in reranked:
        p = r.payload or {}
        start_seconds = int(p.get("start") or 0)
        if p.get("source_type") == "pdf":
            sources.append(
                {
                    "videoId": str(p.get("number")),
                    "videoTitle": p.get("title"),
                    "timestamp": f"Page ~{p.get('page_estimate', 0)}",
                    "similarity": round(r.score, 3),
                    "text_preview": str(p.get("text", ""))[:150] + "...",
                    "source_type": "pdf",
                    "video_url": None,
                }
            )
        else:
            sources.append(
                {
                    "videoId": str(p.get("number")),
                    "videoTitle": p.get("title"),
                    "timestamp": f"{start_seconds // 60}:{start_seconds % 60:02d}",
                    "timestamp_seconds": start_seconds,
                    "similarity": round(r.score, 3),
                    "text_preview": str(p.get("text", ""))[:150] + "...",
                    "source_type": "video",
                    "video_url": p.get("video_url"),
                }
            )

    suggested_questions = await loop.run_in_executor(
        _executor,
        functools.partial(_suggested_questions, query.message, assistant_reply),
    )

    return {
        "content": assistant_reply,
        "sources": sources,
        "session_id": session_id,
        "suggested_questions": suggested_questions,
    }


# ── Session management ────────────────────────────────────────────────────────


@app.post("/clear-history")
async def clear_history(session_id: str):
    clear_session_messages(session_id)
    return {"success": True}


# ── Resource listing ──────────────────────────────────────────────────────────


@app.get("/videos")
async def get_videos():
    loop = asyncio.get_running_loop()
    resources = await loop.run_in_executor(_executor, get_all_resources, "video")
    if resources:
        return [
            {
                "id": r.id,
                "title": r.title,
                "type": "video",
                "chunk_count": r.chunk_count,
                "indexed_at": r.indexed_at.isoformat(),
                "video_url": r.video_url,
            }
            for r in resources
        ]
    return await loop.run_in_executor(_executor, _scroll_all, "video")


@app.get("/documents")
async def get_documents():
    loop = asyncio.get_running_loop()
    resources = await loop.run_in_executor(_executor, get_all_resources, "pdf")
    if resources:
        return [
            {
                "id": r.id,
                "title": r.title,
                "type": "pdf",
                "chunk_count": r.chunk_count,
                "indexed_at": r.indexed_at.isoformat(),
                "file_size_bytes": r.file_size_bytes,
            }
            for r in resources
        ]
    return await loop.run_in_executor(_executor, _scroll_all, "pdf")


# ── Delete resource ───────────────────────────────────────────────────────────


@app.delete("/resource/{resource_id}")
async def delete_resource_endpoint(resource_id: str):
    loop = asyncio.get_running_loop()

    def _delete_from_qdrant():
        for collection in [COLLECTION_NAME, COLLECTION_NAME_PARENTS]:
            try:
                qdrant_client.delete(
                    collection_name=collection,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="number",
                                    match=models.MatchValue(value=resource_id),
                                )
                            ]
                        )
                    ),
                )
            except Exception as e:
                print(f"Qdrant delete error ({collection}): {e}")

    await loop.run_in_executor(_executor, _delete_from_qdrant)
    deleted = await loop.run_in_executor(_executor, delete_resource, resource_id)
    return {"success": deleted}


# ── Video ingestion ───────────────────────────────────────────────────────────


@app.post("/process")
@limiter.limit("10/minute")
async def process_video(request: Request, req: VideoRequest):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(_executor, process_and_save, req.url)
    if not result:
        return {"success": False}
    if result.get("already_exists"):
        return {"success": False, "reason": "already_exists", "title": result["title"]}
    return {"success": True, "title": result["title"], "chunks": result["chunks"]}


@app.websocket("/ws/process-video")
async def process_video_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        video_url = await websocket.receive_text()
        await websocket.send_text("Starting video processing...")

        loop = asyncio.get_running_loop()
        await websocket.send_text("Downloading audio...")
        result = await loop.run_in_executor(
            _executor, lambda: process_and_save(video_url)
        )
        if result:
            await websocket.send_text(
                f"COMPLETE: {result['title']} ({result['chunks']} chunks)"
            )
            await websocket.send_json(
                {
                    "status": "complete",
                    "title": result["title"],
                    "chunks": result["chunks"],
                }
            )
        else:
            await websocket.send_json({"status": "error"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})


# ── PDF upload ────────────────────────────────────────────────────────────────


@app.post("/upload-pdf")
@limiter.limit("10/minute")
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    safe_filename = os.path.basename(filename).replace("..", "").lstrip("/\\")
    if not safe_filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid filename")

    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", safe_filename)

    try:
        max_bytes = MAX_UPLOAD_MB * 1024 * 1024
        total = 0
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    buffer.close()
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=413, detail=f"File too large. Max {MAX_UPLOAD_MB}MB"
                    )
                buffer.write(chunk)

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(_executor, process_and_save_pdf, file_path)

        if result["success"]:
            os.remove(file_path)
            return {
                "success": True,
                "title": result["title"],
                "pdf_id": result["pdf_id"],
                "chunks": result["chunks"],
            }
        os.remove(file_path)
        raise HTTPException(
            status_code=400, detail=result.get("error", "Processing failed")
        )
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
