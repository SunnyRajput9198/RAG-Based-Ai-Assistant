from sentence_transformers import SentenceTransformer
import joblib
import pandas as pd
from test import get_transcript
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def process_and_save(video_url):
    data = get_transcript(video_url)
    if not data:
        return
    
    chunks = data['chunks']
    title = data['title']
    
    # Embeddings banao
    texts = [c['text'] for c in chunks]
    embeddings = embedding_model.encode(texts).tolist()
    
    for i, chunk in enumerate(chunks):
        chunk['embedding'] = embeddings[i]
        chunk['title'] = title
    
    df = pd.DataFrame.from_records(chunks)
    joblib.dump(df, "data.embeddings.joblib")
    print(f"Saved! {len(chunks)} chunks")

url = input("YouTube URL dalo: ")
process_and_save(url)
