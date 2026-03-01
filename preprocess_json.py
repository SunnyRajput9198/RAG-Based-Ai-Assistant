import os
import json
import pandas as pd
import joblib
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embedding(text_list):
    return model.encode(text_list).tolist()

# Pehle se saved data load karo agar hai
if os.path.exists("data.embeddings.joblib"):
    existing_df = joblib.load("data.embeddings.joblib")
    my_dicts = existing_df.to_dict('records')
    chunk_id = len(my_dicts)
    existing_titles = existing_df['title'].unique().tolist()
    print(f"Existing data: {len(my_dicts)} chunks")
else:
    my_dicts = []
    chunk_id = 0
    existing_titles = []

jsons = os.listdir("jsons")

for json_file in jsons:
    with open(f"jsons/{json_file}") as f:
        content = json.load(f)
    
    # Already processed hai toh skip karo
    title = content['chunks'][0]['title'] if content['chunks'] else None
    if title in existing_titles:
        print(f"Skipping {json_file} - already processed")
        continue

    print(f"Creating Embeddings for {json_file}")
    embeddings = create_embedding([c['text'] for c in content['chunks']])

    for i, chunk in enumerate(content['chunks']):
        chunk['chunk_id'] = chunk_id
        chunk['embedding'] = embeddings[i]
        chunk_id += 1
        my_dicts.append(chunk)

df = pd.DataFrame.from_records(my_dicts)
print(df)
joblib.dump(df, "data.embeddings.joblib")
print("Saved!")