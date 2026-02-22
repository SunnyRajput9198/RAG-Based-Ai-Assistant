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
load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.7)
agent = create_agent(llm, tools=[], checkpointer=InMemorySaver())

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

df = joblib.load('data.embeddings.joblib')
config = {"configurable": {"thread_id": "1"}}

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
    prompt = f'''
Sigma Web Development course ke video chunks:
{new_df[["title", "number", "start", "end", "text"]].to_json(orient="records")}

Question: "{query.message}"

Answer ONLY from the above context.
Include video number and timestamp.
'''

    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config
    )

    # 4️⃣ Sources
    sources = [
        {
            "VideoId": int(row["number"]),
            "videoTitle": row["title"],
            "timestamp": f"{int(row['start']) // 60}:{int(row['start']) % 60:02d}"
        }
        for _, row in new_df.iterrows()
    ]

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
            "id": int(row["number"]),
            "title": row["title"],
            "duration": f"{minutes}:{seconds:02d}"
        })

    return result