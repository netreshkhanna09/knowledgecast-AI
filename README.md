# KnowledgeCast AI

A RAG-powered knowledge synthesis platform that transforms PDFs, research papers, documentation, and web articles into AI-generated summaries and Q&A experiences.

## What it does

- Upload multiple PDFs and/or article URLs as knowledge sources
- Ask questions and get AI-generated answers grounded in your documents
- Generate executive summaries of your entire knowledge base
- Generate focused summaries on specific topics

## Tech Stack

- **Backend**: FastAPI, Python
- **PDF Extraction**: PyMuPDF
- **URL Extraction**: newspaper3k
- **Chunking**: LangChain RecursiveCharacterTextSplitter
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Store**: FAISS
- **LLM**: Groq API (Llama 3.3 70B)
- **Frontend**: Streamlit (coming soon)

## How RAG Works in This Project

```
PDFs + URLs → Text Extraction → Chunking → Embeddings → FAISS Index
                                                              ↓
User Question → Embedding → FAISS Search → Relevant Chunks → Groq LLM → Answer
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /process-sources | Upload PDFs and URLs, build knowledge base |
| POST | /ask | Ask a question, get AI answer |
| POST | /generate-summary | Generate full knowledge base summary |
| POST | /topic-summary | Generate topic-focused summary |

## Run Locally

```bash
git clone https://github.com/netreshkhanna09/knowledgecast-AI
cd knowledgecast-AI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Add your Groq API key to `.env`:
```
GROQ_API_KEY=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
```

## Project Status

Currently building — Day 14 of 30 day build schedule.
RAG-powered platform that transforms PDFs and articles
into summaries, podcasts and audiobooks.