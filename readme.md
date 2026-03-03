# EduBot - AI Teaching Assistant

An AI-powered teaching assistant that lets you chat with your course videos and documents using RAG (Retrieval-Augmented Generation).

![EduBot](https://img.shields.io/badge/AI-Claude%20Sonnet%204-blue) ![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green) ![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)

## Features

- 🎥 **YouTube Video Processing** — Paste a YouTube URL, audio gets downloaded, transcribed, and indexed automatically
- 📄 **PDF Upload & Search** — Upload PDF documents and ask questions from them
- 🤖 **RAG-based Q&A** — Answers grounded in your actual video/document content using Claude Sonnet 4
- 💬 **Conversation Memory** — Remembers previous questions in a session
- 🔗 **Clickable Timestamps** — Sources show exact video timestamps
- 💡 **Suggested Questions** — Auto-generates follow-up questions after each answer
- ⚡ **Real-time Progress** — WebSocket-based live progress during video processing

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python |
| AI | Claude Sonnet 4 (Anthropic) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Transcription | OpenAI Whisper (CPU) |
| Audio Download | yt-dlp |
| Memory | LangGraph InMemorySaver |
| Vector Search | scikit-learn cosine similarity |
| Storage | joblib (local) |

## Project Structure

```
RAG-Based-Ai-Assistant/
├── api.py                  # FastAPI backend
├── create_chunks.py        # YouTube/audio transcription pipeline
├── preprocess_json.py      # Embedding generation
├── process_youtube.py      # YouTube processor (used by API)
├── process_pdf.py          # PDF processor
├── jsons/                  # Transcript JSON files
├── audios/                 # Temporary audio files
├── data.embeddings.joblib  # Vector store
├── frontend/               # Next.js app
└── .env                    # API keys
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/SunnyRajput9198/RAG-Based-Ai-Assistant.git
cd RAG-Based-Ai-Assistant
```

### 2. Backend Setup

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

Create `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Add Content

```bash
# Transcribe a YouTube video
python create_chunks.py
# Paste YouTube URL when prompted

# Generate embeddings
python preprocess_json.py
```

### 4. Start Backend

```bash
uvicorn api:app --reload
# Runs on http://localhost:8000
```

### 5. Start Frontend

```bash
cd frontend
npm install
npx next dev
# Runs on http://localhost:3000
```

## How It Works

```
YouTube URL → yt-dlp → Whisper (transcription) → JSON chunks
                                                        ↓
PDF Upload → text extraction → JSON chunks      → Embeddings
                                                        ↓
User Question → Embedding → Cosine Similarity → Top 5 chunks
                                                        ↓
                                              Claude Sonnet 4
                                                        ↓
                                    Answer + Sources + Suggestions
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Ask a question |
| GET | `/videos` | List all videos |
| GET | `/documents` | List all PDFs |
| POST | `/process` | Add YouTube video |
| POST | `/upload-pdf` | Upload PDF |
| WS | `/ws/process-video` | Real-time video processing |
| POST | `/clear-history` | Clear chat history |

## Requirements

- Python 3.11+
- Node.js 18+
- ffmpeg (for audio processing)
- Anthropic API key

## License

MIT