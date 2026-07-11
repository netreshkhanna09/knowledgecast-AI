# 🎙️ KnowledgeCast AI

> **A RAG-powered knowledge synthesis platform that transforms  blogs, articles, url, PDFs, research papers into podcasts, audiobooks, smart summaries, and Q&A experiences.**

---

## 🌐 Live Demo

| | Link |
|---|---|
| 🖥️ **Frontend (Streamlit)** | [knowledgecast-ai.streamlit.app](https://knowledgecast-ai-cj9njr2werp5ob5ngfpjpq.streamlit.app) |
| ⚙️ **Backend API (FastAPI Docs)** | [netreshkhanna09-knowledgecast-ai.hf.space/docs](https://netreshkhanna09-knowledgecast-ai.hf.space/docs) |

---

## 📌 What is KnowledgeCast AI

Most people struggle to extract useful knowledge from large volumes of documents. Reading through 10 research papers, 5 blog posts, and 3 documentation PDFs to find answers takes hours.

KnowledgeCast AI solves this. Upload any combination of PDFs and URLs — research papers, company reports, blog articles, technical documentation, legal documents, anything — and the platform builds a unified AI-powered knowledge base that lets you:

- Get instant answers to specific questions grounded in your documents
- Generate executive summaries of everything you uploaded
- Summarize any specific topic across all your sources
- Convert your knowledge base into a fully produced two-host podcast with audio
- Convert your knowledge base into a narrated audiobook with audio
- Revisit everything you generated through a built-in history system

---

## ✨ Features

### 📥 Multi-Source Ingestion
- Upload multiple PDFs simultaneously
- Add multiple article/blog URLs
- Mix PDFs and URLs in a single knowledge base
- Partial success handling — one bad source doesn't fail everything
- Source metadata preserved throughout the pipeline

### 🔍 RAG-Powered Q&A
- Ask any question about your uploaded content
- Answers grounded strictly in your documents — no hallucination
- Source citations with every answer
- Configurable context depth (3–10 chunks)

### 📄 Smart Summarization
- Full knowledge base executive summary
- Topic-specific summaries with semantic retrieval
- Structured output — executive summary, key insights, main takeaways
- Similarity threshold filtering to prevent off-topic generation

### 🎙️ AI Podcast Generation
- Two-host conversational format (Alex + Sam)
- User-defined duration — 2, 5, 10, or 15 minutes
- Topic-focused generation from your knowledge base
- Full MP3 audio output, playable directly in browser
- Real-time progress streaming via SSE

### 📖 AI Audiobook Generation
- Single-narrator educational format
- User-defined duration — 2, 5, 10, or 15 minutes
- Topic-focused narration from your knowledge base
- Full MP3 audio output, playable directly in browser
- Real-time progress streaming via SSE

### 🕓 Generation History
- Every generation saved automatically to SQLite
- Filter by type — podcast, audiobook, summary, Q&A
- Replay audio from past generations
- Delete individual records

### 📡 Real-Time Progress Tracking
- Live SSE streaming for long operations
- Stage-by-stage updates — Retrieving → Scripting → Audio → Done
- No frozen spinners — users always know what's happening

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | FastAPI + Python | REST API, endpoint routing |
| **Frontend** | Streamlit | User interface |
| **PDF Extraction** | PyMuPDF | Text extraction from digital PDFs |
| **URL Extraction** | newspaper3k | Clean article text from web URLs |
| **Text Chunking** | LangChain RecursiveCharacterTextSplitter | Split text into overlapping chunks |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) | Convert text to 384-dim vectors |
| **Vector Store** | FAISS | Fast semantic similarity search |
| **LLM** | Groq API + Llama 3.3 70B | Content generation, Q&A, summaries |
| **Text-to-Speech** | gTTS | MP3 audio generation |
| **Database** | SQLite + SQLAlchemy | Generation history storage |
| **Real-Time** | Server-Sent Events (SSE) | Live progress streaming |
| **Deployment** | Hugging Face Spaces (Docker) + Streamlit Cloud | Backend + Frontend hosting |

---

## 🧠 How RAG Works in This Project

```
┌─────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                       │
│                                                             │
│  PDFs + URLs                                                │
│      ↓                                                      │
│  Text Extraction (PyMuPDF / newspaper3k)                    │
│      ↓                                                      │
│  Text Cleaning                                              │
│      ↓                                                      │
│  Chunking (700 tokens, 100 overlap)                         │
│      ↓                                                      │
│  Embedding Generation (all-MiniLM-L6-v2 → 384 dimensions)  │
│      ↓                                                      │
│  FAISS Index Built + Saved to Disk                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     RETRIEVAL PIPELINE                       │
│                                                             │
│  User Query / Topic                                         │
│      ↓                                                      │
│  Query → Embedding Vector                                   │
│      ↓                                                      │
│  FAISS Similarity Search → Top-K Relevant Chunks            │
│      ↓                                                      │
│  Similarity Threshold Filter (score > 0.3)                  │
│      ↓                                                      │
│  Context Assembly                                           │
│      ↓                                                      │
│  Groq LLM (Llama 3.3 70B) → Generated Output               │
│      ↓                                                      │
│  Summary / Answer / Podcast Script / Audiobook Script       │
│      ↓  (for audio outputs)                                 │
│  gTTS → MP3 Audio File                                      │
└─────────────────────────────────────────────────────────────┘
```

**Why RAG and not just an LLM?**

- LLMs have a context window limit (~8000 tokens). A 50-page PDF is ~150,000 characters — it simply won't fit.
- RAG retrieves only the most relevant 5–8 chunks (~1500 words) for any given query, fitting perfectly within the context window.
- RAG prevents hallucination — the LLM only answers from your actual documents, not from general training knowledge.
- RAG enables topic-focused generation — "generate a podcast about the attention mechanism" finds only attention-related chunks across all your sources and generates from those specifically.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/health` | Service status |
| POST | `/process-sources` | Upload PDFs + URLs, run full ingestion pipeline |
| POST | `/ask` | Q&A with source citations |
| POST | `/generate-summary` | Full knowledge base summary |
| POST | `/topic-summary` | Topic-focused summary |
| POST | `/generate-podcast-script` | Podcast script only |
| POST | `/generate-podcast` | Full podcast — script + MP3 |
| POST | `/generate-podcast-stream` | Full podcast with SSE progress |
| POST | `/generate-audiobook-script` | Audiobook script only |
| POST | `/generate-audiobook` | Full audiobook — script + MP3 |
| POST | `/generate-audiobook-stream` | Full audiobook with SSE progress |
| GET | `/download-audio/{filename}` | Download generated MP3 |
| GET | `/history` | Fetch all past generations |
| GET | `/history/{id}` | Fetch single generation |
| DELETE | `/history/{id}` | Delete a generation record |

---

## 🚀 Run Locally

### Prerequisites
- Python 3.11+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Setup

```bash
# clone the repo
git clone https://github.com/netreshkhanna09/knowledgecast-AI
cd knowledgecast-AI

# create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# install dependencies
pip install -r requirements.txt

# create .env file
echo GROQ_API_KEY=your_key_here > .env
```

### Run Backend

```bash
uvicorn backend.main:app --reload
```

API runs at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### Run Frontend

```bash
streamlit run frontend/app.py
```

Frontend runs at `http://localhost:8501`

---

## 📁 Project Structure

```
knowledgecast-AI/
├── backend/
│   ├── main.py                    ← FastAPI app, all endpoints
│   └── services/
│       ├── pdf_service.py         ← PyMuPDF text extraction
│       ├── url_service.py         ← newspaper3k URL extraction
│       ├── chunk_service.py       ← LangChain text chunking
│       ├── embedding_service.py   ← Sentence Transformers embeddings
│       ├── rag_service.py         ← FAISS build + retrieval
│       ├── llm_service.py         ← Groq LLM calls + prompt engineering
│       ├── audio_service.py       ← gTTS audio generation
│       └── database_service.py    ← SQLite history (SQLAlchemy)
├── frontend/
│   └── app.py                     ← Streamlit UI
├── uploads/                       ← Uploaded PDFs (temp)
├── audio/                         ← Generated MP3 files (temp)
├── vector_store/                  ← FAISS index + chunks JSON (temp)
├── .env                           ← API keys (never committed)
├── .gitignore
├── requirements.txt
├── Procfile                       ← Render deployment config
└── README.md
```

---

## ⚠️ Known Limitations

**Ephemeral Storage** — The free deployment tier uses ephemeral storage. Uploaded files, the FAISS index, and generated audio are wiped on server restart. Users need to re-upload sources each session. This is a free-tier infrastructure constraint, not a design limitation — in a production deployment with persistent storage (S3, GCS, or a paid server), this would not be an issue.

**Scanned PDFs** — PyMuPDF can only extract text from digital PDFs (created from Word, Google Docs, etc.). Scanned document PDFs (photos of physical pages) require OCR, which is not implemented in V1.

**Free Tier Spin-Down** — The Hugging Face Space may take 30–60 seconds to wake up after inactivity. This is normal free-tier behaviour.

---


## 👨‍💻 Author

**Netresh Khanna**
[GitHub](https://github.com/netreshkhanna09) · [LinkedIn](https://linkedin.com/in/netreshkhanna09)