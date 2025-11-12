import requests
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

import json
import pandas as pd
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from dotenv import load_dotenv

load_dotenv()

# def create_embedding(text_list):
#     # https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
#     r = requests.post("http://localhost:11434/api/embed", json={
#         "model": "bge-m3",
#         "input": text_list
#     })

#     embedding = r.json()["embeddings"] 
#     return embedding

# Alternative using LangChain (simpler approach)
def create_embedding_langchain(text_list):
    """
    Create embeddings using LangChain's GoogleGenerativeAIEmbeddings wrapper.
    """
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    embeddings = embedding_model.embed_documents(text_list)
    return embeddings

embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

jsons = os.listdir("newjsons")  # List all the jsons 
my_dicts = []
chunk_id = 0

for json_file in jsons:
    with open(f"newjsons/{json_file}") as f:
        content = json.load(f)
    print(f"Creating Embeddings for {json_file}")
    embeddings = create_embedding_langchain([c['text'] for c in content['chunks']])
       
    for i, chunk in enumerate(content['chunks']):
        chunk['chunk_id'] = chunk_id
        chunk['embedding'] = embeddings[i]
        chunk_id += 1
        my_dicts.append(chunk) 
    # break
# print(my_dicts)

df = pd.DataFrame.from_records(my_dicts)
print(df)
joblib.dump(df, "data.embeddings.joblib")
# a = create_embedding(["Cat sat on the mat", "Harry dances on a mat"])
# print(a)
