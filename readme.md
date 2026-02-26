# 🎓 RAG-Based AI Teaching Assistant

A powerful **Retrieval-Augmented Generation (RAG)** based AI assistant that learns from your own video content and answers questions based on it. Built with Google Gemini, LangChain, and Whisper.

---



## 🚀 Features

- 🎥 Converts video lectures into searchable knowledge
- 🔊 Transcribes audio using OpenAI Whisper
- 🧠 Generates embeddings using Google Generative AI
- 🔍 Retrieves the most relevant context using cosine similarity
- 💬 Answers questions using Google Gemini LLM

---

## 🛠️ Installation

```bash
git clone https://github.com/SunnyRajput9198/RAG-Based-Ai-Assistant.git
cd RAG-Based-Ai-Assistant
python -m venv venv
source venv/Scripts/activate  # On Windows
pip install -r requirements.txt
```

Create a `.env` file in the root directory and add your API key:

```
GOOGLE_API_KEY=your_google_api_key_here
```

---

## 📋 How to Use

### Step 1 — Collect Your Videos
Move all your video files into the `videos/` folder.

### Step 2 — Convert Videos to MP3
Run the following script to extract audio from all video files:

```bash
python video_to_mp3.py
```

### Step 3 — Transcribe MP3 to JSON
Convert all MP3 files to structured JSON transcripts using Whisper:

```bash
python mp3_to_json.py
```

### Step 4 — Generate Embeddings
Process the JSON transcripts into a vector dataframe and save it as a joblib pickle:

```bash
python preprocess_json.py
```

### Step 5 — Ask Questions
Load the embeddings, find the most relevant context, and query the LLM:

```bash
python read_chunks.py
```

---

## 🗂️ Project Structure

```
RAG-Based-Ai-Assistant/
│
├── videos/               # Input video files
├── audios/               # Extracted MP3 files
├── jsons/                # Whisper transcription output
├── video_to_mp3.py       # Video to audio converter
├── mp3_to_json.py        # Audio to JSON transcriber
├── preprocess_json.py    # Embedding generator
├── read_chunks.py        # RAG query engine
├── data.embeddings.joblib # Vector store (gitignored)
├── requirements.txt      # Dependencies
└── .env                  # API keys (gitignored)
```

---

## 🧰 Tech Stack

| Tool | Purpose |
|------|---------|
| OpenAI Whisper | Audio transcription |
| Google Gemini | LLM for answer generation |
| LangChain | LLM framework |
| Scikit-learn | Cosine similarity search |
| Joblib | Embedding storage |
| Python-dotenv | Environment management |

---

## 👨‍💻 Author

**Sunny Rajput** — [GitHub](https://github.com/SunnyRajput9198)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
