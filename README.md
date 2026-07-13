---
title: KnowledgeCast AI
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

<div align="center">

# 🎙️ KnowledgeCast AI

### From any PDF, URL, blog, or article — to a podcast, audiobook, summary, or Q&A session.

Drop in your sources. KnowledgeCast AI builds a semantic knowledge base, retrieves what's relevant, and generates content you can actually consume — a two-host podcast, a narrated audiobook, a structured summary, or direct answers to your questions. All grounded in your documents through RAG. No hallucination. No guessing. Every generation is saved to history so you can replay audio and revisit content anytime. Real-time progress streaming via SSE keeps you informed at every step — no frozen spinners, no waiting in the dark.

<br/>

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://knowledgecast-ai-cj9njr2werp5ob5ngfpjpq.streamlit.app)
&nbsp;
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-85EA2D?style=flat-square&logo=swagger&logoColor=black)](https://netreshkhanna09-knowledgecast-ai.hf.space/docs)
&nbsp;
[![GitHub](https://img.shields.io/badge/GitHub-Source-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/netreshkhanna09/knowledgecast-AI)

</div>

---

## The Problem

Reading 10 research papers, 5 blog posts, and 3 documentation PDFs to extract specific knowledge takes hours. Most of that time is spent on content that isn't relevant to what you actually need.

KnowledgeCast AI fixes this. Upload your sources once. The platform builds a unified, searchable knowledge base and lets you consume that knowledge in whichever format works best for you — a focused answer, a structured summary, a podcast you can listen to while commuting, or a narrated audiobook.

It works on any content — research papers, company reports, legal documents, technical documentation, news articles, blog posts, anything.

---

## What You Can Do With It

**Ask questions** — type any question and get an answer grounded strictly in your uploaded documents, with source citations.

**Generate summaries** — get a structured executive summary of your entire knowledge base, or focus on a specific topic.

**Create podcasts** — generate a two-host conversational podcast on any topic from your sources, with full MP3 audio output.

**Create audiobooks** — generate a single-narrator educational audiobook with MP3 audio output.

**Review history** — every generation is saved. Replay audio, re-read content, delete old records — all from a built-in history panel.

---

## How It Works

The core architecture is RAG — Retrieval-Augmented Generation. Instead of sending entire documents to an LLM (which won't fit and causes hallucination), the system finds only the most relevant pieces first, then generates from those.

```
━━━━━━━━━━━━━━━━━━━  INGESTION  ━━━━━━━━━━━━━━━━━━━
                    (runs once)

  PDFs + URLs
       │
       ▼
  Text Extraction
  PyMuPDF for PDFs · newspaper3k for URLs
       │
       ▼
  Chunking
  700 tokens · 100 token overlap · recursive splitting
       │
       ▼
  Embedding
  all-MiniLM-L6-v2 · 384 dimensions per chunk
       │
       ▼
  FAISS Index
  stored on disk · ready for search


━━━━━━━━━━━━━━━━━━━  RETRIEVAL  ━━━━━━━━━━━━━━━━━━━
                  (runs per request)

  User Query / Topic
       │
       ▼
  Query → Embedding Vector
       │
       ▼
  FAISS Similarity Search
  top-K chunks · relevance score filtering
       │
       ▼
  Groq · Llama 3.3 70B
  context-grounded generation
       │
       ▼
  Answer · Summary · Script
       │
       ▼  (audio outputs only)
  gTTS · MP3
```

**Why not just send everything to the LLM?**

A research paper is typically 80,000–150,000 characters. Llama 3's context window handles roughly 8,000 tokens. The document simply doesn't fit. Even if it did, output quality degrades significantly when the context is too large — the LLM gets confused by irrelevant content. RAG retrieves only the 5–8 most semantically relevant chunks for any given query, keeping context focused and output accurate.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend API | FastAPI | Fast, async, automatic Swagger docs |
| PDF Extraction | PyMuPDF | Reliable, handles multi-page PDFs efficiently |
| URL Extraction | newspaper3k | Strips nav/ads, extracts article body cleanly |
| Chunking | LangChain RecursiveCharacterTextSplitter | Tries paragraph → sentence → word splits in order |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 | Free, local, 384-dim vectors, strong semantic quality |
| Vector Store | FAISS IndexFlatL2 | No server required, saves to disk in 2 lines, exact search |
| LLM | Groq API + Llama 3.3 70B | Free tier, fast LPU inference, follows prompts reliably |
| Audio | gTTS + pydub | Free, unlimited, no API cost |
| Database | SQLite + SQLAlchemy | Zero setup, file-based, right for single-user demo |
| Progress | Server-Sent Events (SSE) | One-direction streaming, simpler than WebSockets |
| Frontend | Streamlit | Full UI in pure Python |
| Deployment | Hugging Face Spaces (Docker) + Streamlit Cloud | Free hosting for backend and frontend |

---

## Project Structure

```
knowledgecast-AI/
│
├── backend/
│   ├── main.py                  ← FastAPI app · all endpoints · orchestration
│   └── services/
│       ├── pdf_service.py       ← PyMuPDF extraction · scanned PDF detection
│       ├── url_service.py       ← newspaper3k · URL validation · error handling
│       ├── chunk_service.py     ← RecursiveCharacterTextSplitter · metadata
│       ├── embedding_service.py ← Lazy-loaded sentence-transformers · batch encoding
│       ├── rag_service.py       ← FAISS build + retrieval · similarity scoring
│       ├── llm_service.py       ← Groq prompts · Q&A · summary · podcast · audiobook
│       ├── audio_service.py     ← gTTS · pydub · two-voice podcast · MP3 output
│       └── database_service.py  ← SQLAlchemy ORM · history · CRUD
│
├── frontend/
│   └── app.py                   ← Streamlit UI · SSE streaming · audio playback
│
├── Dockerfile                   ← HuggingFace Spaces container config
├── requirements.txt
├── .env                         ← API keys · never committed
└── README.md
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/process-sources` | Upload PDFs + URLs · run full ingestion pipeline |
| `POST` | `/ask` | Q&A with source citations |
| `POST` | `/generate-summary` | Executive summary of full knowledge base |
| `POST` | `/topic-summary` | Focused summary on a specific topic |
| `POST` | `/generate-podcast` | Full podcast pipeline · script + MP3 |
| `POST` | `/generate-podcast-stream` | Same with live SSE progress updates |
| `POST` | `/generate-audiobook` | Full audiobook pipeline · script + MP3 |
| `POST` | `/generate-audiobook-stream` | Same with live SSE progress updates |
| `GET` | `/download-audio/{filename}` | Serve generated MP3 |
| `GET` | `/history` | All past generations |
| `DELETE` | `/history/{id}` | Delete a record |

Full interactive documentation at the [live API](https://netreshkhanna09-knowledgecast-ai.hf.space/docs).

---

## Run Locally

**Requirements** — Python 3.11+, ffmpeg, a free [Groq API key](https://console.groq.com)

```bash
git clone https://github.com/netreshkhanna09/knowledgecast-AI
cd knowledgecast-AI

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

echo "GROQ_API_KEY=your_key_here" > .env

# start backend
uvicorn backend.main:app --reload

# start frontend (separate terminal)
streamlit run frontend/app.py
```

Backend → `http://localhost:8000/docs`
Frontend → `http://localhost:8501`

---

## Design Decisions

**Lazy model loading** — importing sentence-transformers loads PyTorch which consumes ~400MB of RAM immediately. On a 512MB free-tier server, loading at startup crashes the process before handling a single request. The model is imported and loaded on first use instead, letting the server start cleanly.

**Chunk overlap** — without overlap, a sentence split across two chunk boundaries loses context in both. A 100-token overlap means the last 100 tokens of every chunk repeat at the start of the next, making each chunk self-contained and semantically complete.

**Relevance threshold filtering** — FAISS always returns top-K results regardless of how relevant they actually are. Without a minimum similarity score, a query about a topic not covered in the documents would still retrieve chunks and the LLM would hallucinate. A threshold of 0.3 stops this — if nothing is close enough, the system says so honestly instead of making something up.

**Partial success on multi-source ingestion** — if a user uploads 4 PDFs and one URL and the URL fails, the system processes the 4 PDFs and reports the failure clearly. Rejecting the entire request because of one bad source would be a poor experience.

**SSE over WebSockets for progress** — podcast and audiobook generation takes 60–90 seconds. Server-Sent Events stream one-way from server to client — simpler than WebSockets, works over standard HTTP, and exactly right for this use case since the client only needs to receive updates, never send them.

---

## Known Limitations

**Ephemeral storage** — the free deployment tier does not persist files between server restarts. Uploaded PDFs, the FAISS index, and generated audio are cleared on restart. Users need to re-upload sources each session. In a production deployment with persistent storage this would not be an issue.

**Scanned PDFs** — V1 supports digital PDFs only. Scanned documents contain images rather than text and require OCR. OCR support is planned for V2.

**Free tier cold starts** — the Hugging Face Space may take 30–60 seconds to respond after inactivity. Standard free-tier behaviour.

---

<div align="center">

Built by **Netresh Khanna** · B.Tech CS (AI), BIT Mesra

[LinkedIn](https://www.linkedin.com/in/Netresh-Khanna) &nbsp;·&nbsp; [GitHub](https://github.com/netreshkhanna09)

</div>