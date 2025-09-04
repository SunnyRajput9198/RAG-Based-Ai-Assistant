import requests
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import joblib


df=joblib.load("data.embeddings.joblib")
def create_embedding(text_list):
    # https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
    r = requests.post("http://localhost:11434/api/embed", json={
        "model": "bge-m3",
        "input": text_list
    })

    embedding = r.json()["embeddings"] 
    return embedding
incoming_query=input("Ask me a question: ")
question_embedding = create_embedding([incoming_query])[0]
print(question_embedding)

# find similarity between question embedding and other embeddings
# print(np.vstack(df["embeddings"].values))
# print(np.vstack(df["embeddings"].shape))
similarities = cosine_similarity(np.vstack(df['embedding']), [question_embedding]).flatten()
print(similarities)
top_results = 3
max_indx = similarities.argsort()[::-1][0:top_results]
print(max_indx)
new_df = df.loc[max_indx] 
print(new_df[["title", "number", "text"]])