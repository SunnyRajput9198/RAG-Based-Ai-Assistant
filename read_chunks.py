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

jsons = os.listdir("jsons")
my_dicts = []
chunk_id = 0

for json_file in jsons:
    with open(f"jsons/{json_file}") as f:
        content = json.load(f)
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