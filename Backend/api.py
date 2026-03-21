from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import os, shutil, json, asyncio, uuid, concurrent.futures
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from process_youtube import process_and_save
from process_pdf import process_and_save_pdf
from qdrant_client import QdrantClient, models
from typing import Optional, List, Dict

load_dotenv()

qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=60)
COLLECTION_NAME = "edubot"

model = SentenceTransformer('all-MiniLM-L6-v2')
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.7)
agent = create_agent(llm, tools=[], checkpointer=InMemorySaver())

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

conversation_store: Dict[str, List[Dict[str, str]]] = {}

def get_embedding(text):
    return np.nan_to_num(model.encode([text])[0])

class Query(BaseModel):
    message: str
    VideoId: Optional[str] = None
    session_id: Optional[str] = None

class VideoRequest(BaseModel):
    url: str


@app.post("/chat")
async def chat(query: Query):
    session_id = query.session_id or str(uuid.uuid4())
    if session_id not in conversation_store:
        conversation_store[session_id] = []

    results = qdrant_client.query_points(
    collection_name=COLLECTION_NAME,
    query=get_embedding(query.message).tolist(),
    limit=5,
    query_filter=models.Filter(
        must=[models.FieldCondition(key="number", match=models.MatchValue(value=query.VideoId))]
    ) if query.VideoId else None
).points

    if not results:
        return {"content": "No content found.", "sources": [], "session_id": session_id}

    history_text = ""
    if conversation_store[session_id]:
        history_text = "\n\nPrevious Conversation:\n"
        for msg in conversation_store[session_id][-6:]:
            role = "Student" if msg["role"] == "user" else "EduBot"
            history_text += f"{role}: {msg['content']}\n"

    chunks_json = json.dumps([{
        "title": r.payload.get("title"),
        "number": r.payload.get("number"),
        "start": r.payload.get("start"),
        "end": r.payload.get("end"),
        "text": r.payload.get("text")
    } for r in results])

    prompt = f'''You are EduBot, an AI teaching assistant for the Sigma Web Development course.

Use ONLY the following video/document chunks to answer the question:
{chunks_json}
{history_text}

Current Question: "{query.message}"

Instructions:
- Answer clearly and in detail based on the context above
- If this question relates to previous conversation, acknowledge and build upon it
- Mention the video/document title and timestamp where relevant
- If answer not in context, say "I don't have information about this in the current videos/documents"
- Use simple language, explain like a teacher
'''

    config = {"configurable": {"thread_id": session_id}}
    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config)
    assistant_reply = response["messages"][-1].content

    conversation_store[session_id].append({"role": "user", "content": query.message})
    conversation_store[session_id].append({"role": "assistant", "content": assistant_reply})

    sources = []
    for r in results:
        p = r.payload
        start_seconds = int(p.get('start') or 0)
        source_type = p.get("source_type", "video")
        if source_type == "pdf":
            sources.append({"videoId": str(p.get("number")), "videoTitle": p.get("title"), "timestamp": f"Page ~{p.get('page_estimate', 0)}", "similarity": round(r.score, 3), "text_preview": str(p.get("text", ""))[:150] + "...", "source_type": "pdf", "video_url": None})
        else:
            sources.append({"videoId": str(p.get("number")), "videoTitle": p.get("title"), "timestamp": f"{start_seconds // 60}:{start_seconds % 60:02d}", "timestamp_seconds": start_seconds, "similarity": round(r.score, 3), "text_preview": str(p.get("text", ""))[:150] + "...", "source_type": "video", "video_url": p.get("video_url")})

    suggested_questions = []
    try:
        suggestion_prompt = f'Based on: Q: "{query.message}" A: "{assistant_reply[:300]}"\nGenerate 3 follow-up questions, one per line, no numbering.'
        sugg = agent.invoke({"messages": [{"role": "user", "content": suggestion_prompt}]}, config)
        suggested_questions = [q.strip().lstrip('*-. 123456789') for q in sugg["messages"][-1].content.strip().split('\n') if q.strip() and len(q.strip()) > 10][:3]
    except: pass

    return {"content": assistant_reply, "sources": sources, "session_id": session_id, "suggested_questions": suggested_questions}


@app.post("/clear-history")
async def clear_history(session_id: str):
    if session_id in conversation_store:
        conversation_store[session_id] = []
        return {"success": True}
    return {"success": False}


@app.get("/videos")
async def get_videos():
    results = qdrant_client.scroll(collection_name=COLLECTION_NAME, limit=10000, with_payload=True, with_vectors=False)[0]
    seen = {}
    for r in results:
        p = r.payload
        if p.get("source_type") != "pdf" and p.get("number") not in seen:
            seen[p["number"]] = {"id": str(p["number"]), "title": p["title"], "type": "video"}
    return list(seen.values())


@app.get("/documents")
async def get_documents():
    results = qdrant_client.scroll(collection_name=COLLECTION_NAME, limit=10000, with_payload=True, with_vectors=False)[0]
    seen = {}
    for r in results:
        p = r.payload
        if p.get("source_type") == "pdf" and p.get("number") not in seen:
            seen[p["number"]] = {"id": str(p["number"]), "title": p["title"], "type": "pdf"}
    return list(seen.values())


@app.post("/process")
async def process_video(req: VideoRequest):
    result = process_and_save(req.url)
    if result:
        return {"success": True, "title": result["title"], "chunks": result["chunks"]}
    return {"success": False}


@app.websocket("/ws/process-video")
async def process_video_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        video_url = await websocket.receive_text()
        await websocket.send_text("Starting video processing...")
        try:
            from process_youtube_with_progress import process_and_save as process_with_progress
        except ImportError:
            process_with_progress = process_and_save
        loop = asyncio.get_event_loop()
        await websocket.send_text("Downloading audio...")
        result = await loop.run_in_executor(concurrent.futures.ThreadPoolExecutor(), lambda: process_with_progress(video_url))
        if result:
            await websocket.send_text(f"COMPLETE: {result['title']} ({result['chunks']} chunks)")
            await websocket.send_json({"status": "complete", "title": result['title'], "chunks": result['chunks']})
        else:
            await websocket.send_json({"status": "error"})
    except WebSocketDisconnect: pass
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        result = process_and_save_pdf(file_path)
        if result['success']:
            os.remove(file_path)
            return {"success": True, "title": result['title'], "pdf_id": result['pdf_id'], "chunks": result['chunks']}
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=result.get('error', 'Processing failed'))
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")