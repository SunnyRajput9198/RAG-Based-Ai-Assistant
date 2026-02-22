import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np 
import joblib 
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
load_dotenv()

agent = create_agent(
    "models/gemini-2.5-flash",
    tools=[],
    checkpointer=InMemorySaver(),
)
config = {"configurable": {"thread_id": "1"}}

embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004"
)

def create_embedding(text_list):
    return embedding_model.embed_documents(text_list)

df = joblib.load('data.embeddings.joblib')

while True:
    incoming_query = input("You: ")
    if incoming_query.lower() == "quit":
        break

    question_embedding = create_embedding([incoming_query])[0]
    similarities = cosine_similarity(np.vstack(df['embedding']), [question_embedding]).flatten()
    max_indx = similarities.argsort()[::-1][:5]
    new_df = df.loc[max_indx]

    prompt = f'''I am teaching web development in my Sigma web development course. Here are video subtitle chunks containing video title, video number, start time in seconds, end time in seconds, the text at that time:

{new_df[["title", "number", "start", "end", "text"]].to_json(orient="records")}
---------------------------------
"{incoming_query}"
Answer in a human way, mention which video and timestamp covers this topic. If unrelated to the course, politely decline.'''

    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config
    )
    print(f"\nAssistant: {response['messages'][-1].content}\n")