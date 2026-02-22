import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np 
import joblib 
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.7)
agent = create_agent(llm, tools=[], checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "1"}}

def create_embedding(text_list):
    return model.encode(text_list).tolist()

df = joblib.load('data.embeddings.joblib')

while True:
    incoming_query = input("You: ")
    if incoming_query.lower() == "quit":
        break

    question_embedding = create_embedding([incoming_query])[0]
    similarities = cosine_similarity(np.vstack(df['embedding']), [question_embedding]).flatten()
    new_df = df.loc[similarities.argsort()[::-1][:5]]

    prompt = f'''I am teaching web development in my Sigma web development course. Here are video subtitle chunks:
{new_df[["title", "number", "start", "end", "text"]].to_json(orient="records")}
Question: "{incoming_query}"
Answer in a human way, mention which video and timestamp covers this topic. If unrelated, politely decline.'''

    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config)
    print(f"\nAssistant: {response['messages'][-1].content}\n")