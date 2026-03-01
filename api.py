from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from process_youtube import process_and_save


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
    VideoId: int|None=None

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

    # 4️⃣ Sources
    # 4️⃣ Sources with similarity scores
    sources = []
    for idx, (_, row) in enumerate(new_df.iterrows()):
        original_idx = top_indices[idx]  # Get original index
        similarity_score = similarities[original_idx]  # Get similarity
    
        sources.append({
        "videoId": str(row["number"]),
        "videoTitle": row["title"],
        "timestamp": f"{int(row['start']) // 60}:{int(row['start']) % 60:02d}",
        "similarity": round(float(similarity_score), 3),  # Add this
        "text_preview": row["text"][:150] + "..."  # Add this (first 150 chars)
    })

    return {
        "content": response["messages"][-1].content,
        "sources": sources
    }

@app.get("/videos")
async def get_videos():
    videos = (
        df[["number", "title", "start", "end"]]
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
    "duration": f"{minutes}:{seconds:02d}"
})

    return result

@app.post("/process")
async def process_video(req: VideoRequest):
    global df
    result = process_and_save(req.url)
    if result:
        df = joblib.load('data.embeddings.joblib')  # reload
        return {"success": True, "title": result["title"], "chunks": result["chunks"]}
    return {"success": False}