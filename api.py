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


load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.7)
agent = create_agent(llm, tools=[], checkpointer=InMemorySaver())

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

df = joblib.load('data.embeddings.joblib')
config = {"configurable": {"thread_id": "1"}}

class VideoRequest(BaseModel):
    url: str

def get_embedding(text):
    return model.encode(text).tolist()

class Query(BaseModel):
    message: str
    VideoId: int | None = None

@app.post("/chat")
async def chat(query: Query):
    # 1️⃣ Decide search space
    search_df = df

    if query.VideoId is not None:
        search_df = df[df["number"] == query.VideoId]

        # Safety check
        if search_df.empty:
            return {
                "content": "No content found for the selected video.",
                "sources": []
            }

    # 2️⃣ Compute similarity
    question_embedding = get_embedding(query.message)
    similarities = cosine_similarity(
        np.vstack(search_df['embedding']),
        [question_embedding]
    ).flatten()

    top_indices = similarities.argsort()[::-1][:5]
    new_df = search_df.iloc[top_indices]

    # 3️⃣ Prompt
    prompt = f'''You are EduBot, an AI teaching assistant for the Sigma Web Development course.

Use ONLY the following video transcript chunks to answer the question:
{new_df[["title", "number", "start", "end", "text"]].to_json(orient="records")}

User Question: "{query.message}"

Instructions:
- Answer clearly and in detail based on the context above
- Mention the video title and timestamp where relevant
- If the answer is not in the context, say "I don't have information about this in the current videos"
- Use simple language, explain like a teacher
'''

    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config
    )

    # 4️⃣ Sources with similarity scores
    sources = []
    for idx, (_, row) in enumerate(new_df.iterrows()):
        original_idx = top_indices[idx]
        similarity_score = similarities[original_idx]
        
        # Check if source is PDF or video
        source_type = row.get('source_type', 'video')
        
        if source_type == 'pdf':
            # PDF source - no timestamp, show page estimate
            sources.append({
                "videoId": str(row["number"]),
                "videoTitle": row["title"],
                "timestamp": f"Page ~{row.get('page_estimate', 0)}",
                "similarity": round(float(similarity_score), 3),
                "text_preview": row["text"][:150] + "...",
                "source_type": "pdf"
            })
        else:
            # Video source - with timestamp
            sources.append({
                "videoId": str(row["number"]),
                "videoTitle": row["title"],
                "timestamp": f"{int(row['start']) // 60}:{int(row['start']) % 60:02d}",
                "similarity": round(float(similarity_score), 3),
                "text_preview": row["text"][:150] + "...",
                "source_type": "video"
            })

    return {
        "content": response["messages"][-1].content,
        "sources": sources
    }

@app.get("/videos")
async def get_videos():
    """Get all videos"""
    # Check if 'start' column exists (videos have start/end, PDFs don't)
    if 'start' not in df.columns:
        return []
    
    videos = (
        df[df['start'].notna()][["number", "title", "start", "end"]]
        .drop_duplicates(subset=["number"])
        .sort_values("number")
    )

    result = []
    for _, row in videos.iterrows():
        duration_sec = int(row["end"] - row["start"])
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
    # Filter only PDFs
    if 'source_type' not in df.columns:
        return []
    
    pdf_df = df[df['source_type'] == 'pdf']
    
    documents = (
        pdf_df[["number", "title"]]
        .drop_duplicates(subset=["number"])
    )

    result = []
    for _, row in documents.iterrows():
        # Count chunks for this PDF
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
        df = joblib.load('data.embeddings.joblib')  # reload
        return {"success": True, "title": result["title"], "chunks": result["chunks"]}
    return {"success": False}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file
    
    Returns:
        success: bool
        title: str
        pdf_id: str
        chunks: int
    """
    global df
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)
    
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Process PDF
    try:
        result = process_and_save_pdf(file_path)
        
        if result['success']:
            # Reload embeddings
            df = joblib.load('data.embeddings.joblib')
            
            # Clean up uploaded file
            os.remove(file_path)
            
            return {
                "success": True,
                "title": result['title'],
                "pdf_id": result['pdf_id'],
                "chunks": result['chunks']
            }
        else:
            # Clean up on failure
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=result.get('error', 'Processing failed'))
            
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")