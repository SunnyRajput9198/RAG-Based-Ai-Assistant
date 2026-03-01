from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import shutil
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from process_youtube import process_and_save
from process_pdf import process_and_save_pdf
import uuid
from typing import Optional, List, Dict

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.7)
agent = create_agent(llm, tools=[], checkpointer=InMemorySaver())

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

df = joblib.load('data.embeddings.joblib')
# ─── Add this helper near the top (after imports) ───────────────────────────
def sanitize_float(value, default=0.0):
    """Replace NaN/Inf with a safe default."""
    try:
        f = float(value)
        if np.isnan(f) or np.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default
    
def sanitize_val(value):
    """Convert NaN/Inf pandas values to None for JSON safety."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
# 🧠 CONVERSATION MEMORY STORE
# Format: {session_id: [{"role": "user", "content": "..."}, ...]}
conversation_store: Dict[str, List[Dict[str, str]]] = {}

def get_embedding(text):
    embedding = model.encode([text])[0]   # always 1D vector
    embedding = np.nan_to_num(embedding)  # remove NaN / Inf
    return embedding
class Query(BaseModel):
    message: str
    VideoId: int | None = None
    session_id: Optional[str] = None  # 🆕 Session tracking

class VideoRequest(BaseModel):
    url: str

@app.post("/chat")
async def chat(query: Query):
    # ════════════════════════════════════════════════════════════════
    # 1️⃣ SESSION MANAGEMENT
    # ════════════════════════════════════════════════════════════════
    session_id = query.session_id or str(uuid.uuid4())
    
    # Initialize session if new
    if session_id not in conversation_store:
        conversation_store[session_id] = []
    
    # Get conversation history (last 10 messages for context)
    conversation_history = conversation_store[session_id][-10:]
    
    # ════════════════════════════════════════════════════════════════
    # 2️⃣ SEARCH SPACE SELECTION
    # ════════════════════════════════════════════════════════════════
    search_df = df
    if query.VideoId is not None:
        search_df = df[df["number"] == query.VideoId]
        if search_df.empty:
            return {
                "content": "No content found for the selected video.",
                "sources": [],
                "session_id": session_id
            }

    # ════════════════════════════════════════════════════════════════
    # 3️⃣ SIMILARITY SEARCH
    # ════════════════════════════════════════════════════════════════
    question_embedding = get_embedding(query.message)
    similarities = cosine_similarity(
        np.vstack(search_df['embedding']),
        [question_embedding]
    ).flatten()

    top_indices = similarities.argsort()[::-1][:5]
    new_df = search_df.iloc[top_indices]

    # ════════════════════════════════════════════════════════════════
    # 4️⃣ BUILD CONTEXT WITH HISTORY
    # ════════════════════════════════════════════════════════════════
    # Format conversation history for context
    history_text = ""
    if conversation_history:
        history_text = "\n\nPrevious Conversation:\n"
        for msg in conversation_history[-6:]:  # Last 3 exchanges
            role = "Student" if msg["role"] == "user" else "EduBot"
            history_text += f"{role}: {msg['content']}\n"
    
    prompt = f'''You are EduBot, an AI teaching assistant for the Sigma Web Development course.

Use ONLY the following video/document chunks to answer the question:
{new_df[["title", "number", "start", "end", "text"]].to_json(orient="records")}
{history_text}

Current Question: "{query.message}"

Instructions:
- Answer clearly and in detail based on the context above
- If this question relates to previous conversation, acknowledge and build upon it
- Mention the video/document title and timestamp/page where relevant
- If the answer is not in the context, say "I don't have information about this in the current videos/documents"
- Use simple language, explain like a teacher
- Keep your answer concise but complete
'''

    # ════════════════════════════════════════════════════════════════
    # 5️⃣ GET AI RESPONSE
    # ════════════════════════════════════════════════════════════════
    config = {"configurable": {"thread_id": session_id}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config
    )
    
    assistant_reply = response["messages"][-1].content

    # ════════════════════════════════════════════════════════════════
    # 6️⃣ SAVE TO CONVERSATION HISTORY
    # ════════════════════════════════════════════════════════════════
    conversation_store[session_id].append({
        "role": "user",
        "content": query.message
    })
    conversation_store[session_id].append({
        "role": "assistant", 
        "content": assistant_reply
    })
   # ════════════════════════════════════════════════════════════════
    # 7️⃣ BUILD SOURCES WITH CLICKABLE LINKS
    # ════════════════════════════════════════════════════════════════
    sources = []
    for idx, (_, row) in enumerate(new_df.iterrows()):
        original_idx = top_indices[idx]
        similarity_score = round(sanitize_float(similarities[original_idx]), 3)
        source_type = row.get('source_type', 'video')

        if source_type == 'pdf':
            sources.append({
                "videoId": str(row["number"]),
                "videoTitle": str(row["title"]),
                "timestamp": f"Page ~{int(sanitize_float(row.get('page_estimate', 0)))}",
                "similarity": similarity_score,
                "text_preview": str(row["text"])[:150] + "...",
                "source_type": "pdf",
                "video_url": None
            })
        else:
            start_seconds = int(sanitize_float(row.get('start', 0)))
            minutes = start_seconds // 60
            seconds = start_seconds % 60

            sources.append({
                "videoId": str(row["number"]),
                "videoTitle": row["title"],
                "timestamp": f"{minutes}:{seconds:02d}",
                "timestamp_seconds": start_seconds,
                "similarity": similarity_score,
                "text_preview": str(row["text"])[:150] + "...",
                "source_type": "video",
                "video_url": sanitize_val(row.get('video_url'))
            })

    return {
        "content": assistant_reply,
        "sources": sources,
        "session_id": session_id  # 🆕 Return session ID
    }

@app.post("/clear-history")
async def clear_history(session_id: str):
    """Clear conversation history for a session"""
    if session_id in conversation_store:
        conversation_store[session_id] = []
        return {"success": True, "message": "Conversation cleared"}
    return {"success": False, "message": "Session not found"}

@app.get("/videos")
async def get_videos():
    if 'start' not in df.columns:
        return []

    videos = (
        df[df['start'].notna()][["number", "title", "start", "end"]]
        .drop_duplicates(subset=["number"])
        .sort_values("number")
    )

    result = []
    for _, row in videos.iterrows():
        # ✅ Sanitize before int conversion
        duration_sec = int(sanitize_float(row["end"]) - sanitize_float(row["start"]))
        minutes = duration_sec // 60
        seconds = duration_sec % 60

        result.append({
            "id": str(row["number"]),
            "title": row["title"],
            "duration": f"{minutes}:{seconds:02d}",
            "type": "video"
        })

    return result

@app.get("/documents")
async def get_documents():
    """Get all documents (PDFs)"""
    if 'source_type' not in df.columns:
        return []
    
    pdf_df = df[df['source_type'] == 'pdf']
    
    documents = (
        pdf_df[["number", "title"]]
        .drop_duplicates(subset=["number"])
    )

    result = []
    for _, row in documents.iterrows():
        chunk_count = len(df[df['number'] == row['number']])
        
        result.append({
            "id": str(row["number"]),
            "title": row["title"],
            "chunks": chunk_count,
            "type": "pdf"
        })

    return result

@app.post("/process")
async def process_video(req: VideoRequest):
    """Process YouTube video"""
    global df
    result = process_and_save(req.url)
    if result:
        df = joblib.load('data.embeddings.joblib')
        return {"success": True, "title": result["title"], "chunks": result["chunks"]}
    return {"success": False}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    global df
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    os.makedirs("uploads", exist_ok=True)
    
    file_path = f"uploads/{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    try:
        result = process_and_save_pdf(file_path)
        
        if result['success']:
            df = joblib.load('data.embeddings.joblib')
            os.remove(file_path)
            
            return {
                "success": True,
                "title": result['title'],
                "pdf_id": result['pdf_id'],
                "chunks": result['chunks']
            }
        else:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=result.get('error', 'Processing failed'))
            
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")