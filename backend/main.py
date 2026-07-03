import os
import shutil
import json
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.url_service import extract_text_from_url
from backend.services.chunk_service import chunk_sources
from backend.services.embedding_service import generate_embeddings
from backend.services.rag_service import build_knowledge_base, retrieve_context
from backend.services.llm_service import generate_answer, generate_summary, generate_topic_summary, generate_podcast_script

app = FastAPI(
    title="KnowledgeCast AI",
    description="RAG-powered knowledge synthesis platform that transforms PDFs and URLs into summaries, Q&A, and podcasts.",
    version="1.0.0"
)

# ─── helper function ────────────────────────────────────────

def save_upload_file(file: UploadFile) -> str:
    """Save uploaded file to uploads folder and return file path."""
    save_path = f"uploads/{file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return save_path

# ─── health checks ──────────────────────────────────────────

@app.get("/", summary="Root", description="Check if API is running.")
def home():
    return {"status": "ok", "message": "KnowledgeCast AI is running"}

@app.get("/health", summary="Health Check", description="Verify all services are operational.")
def health_check():
    return {"status": "ok"}

# ─── ingestion pipeline ─────────────────────────────────────

@app.post("/process-sources", summary="Process Sources", description="Upload PDFs and/or URLs. Extracts text, chunks, embeds, and builds FAISS knowledge base.")
async def process_sources(
    files: List[UploadFile] = File(default=None),
    urls_input: str = Form(default="")
):
    if files is None:
        files = []

    sources = []
    failed_sources = []

    # step 1 — extract text from PDFs
    for file in files:
        if not file.filename.endswith(".pdf"):
            failed_sources.append({"source": file.filename, "error": "only PDF files are allowed"})
            continue
        save_path = save_upload_file(file)
        try:
            text = extract_text_from_pdf(save_path)
            sources.append({"source_name": file.filename, "source_type": "pdf", "text": text})
        except Exception as e:
            failed_sources.append({"source": file.filename, "error": str(e)})

    # step 2 — extract text from URLs
    if urls_input.strip():
        urls = [url.strip() for url in urls_input.split(",")]
        for url in urls:
            if not url:
                continue
            try:
                result = extract_text_from_url(url)
                sources.append({"source_name": url, "source_type": "url", "text": result["text"]})
            except Exception as e:
                failed_sources.append({"source": url, "error": str(e)})

    if not sources:
        raise HTTPException(status_code=400, detail="No sources could be processed successfully.")

    # step 3 — chunk
    try:
        chunks = chunk_sources(sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunking failed: {str(e)}")

    # step 4 — embed
    try:
        embeddings = generate_embeddings(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

    # step 5 — build FAISS index
    try:
        kb_result = build_knowledge_base(chunks, embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index building failed: {str(e)}")

    return {
        "status": "knowledge base ready",
        "processed_sources": len(sources),
        "failed_sources": len(failed_sources),
        "total_chunks": kb_result["total_vectors"],
        "embedding_dimensions": kb_result["dimensions"],
        "failed_details": failed_sources
    }

# ─── Q&A ────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/ask", summary="Ask a Question", description="Retrieve relevant context from knowledge base and generate AI answer using Groq LLM.")
def ask(request: QueryRequest):
    try:
        chunks = retrieve_context(request.query, request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    context = "\n\n".join([chunk["text"] for chunk in chunks])
    sources_cited = list(set([chunk["source_name"] for chunk in chunks]))

    try:
        answer = generate_answer(request.query, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    return {
        "status": "success",
        "query": request.query,
        "answer": answer,
        "sources_cited": sources_cited,
        "chunks_retrieved": len(chunks)
    }

# ─── summaries ──────────────────────────────────────────────

class SummaryRequest(BaseModel):
    topic: str = ""

@app.post("/generate-summary", summary="Generate Summary", description="Generate executive summary of full knowledge base or a specific topic.")
def generate_summary_endpoint(request: SummaryRequest):
    try:
        if request.topic.strip():
            chunks = retrieve_context(request.topic, top_k=8)
        else:
            with open("vector_store/chunks.json", "r") as f:
                chunks = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    context = "\n\n".join([chunk["text"] for chunk in chunks])

    try:
        summary = generate_summary(context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

    return {
        "status": "success",
        "topic": request.topic if request.topic else "full knowledge base",
        "summary": summary
    }


class TopicSummaryRequest(BaseModel):
    topic: str
    top_k: int = 6

@app.post("/topic-summary", summary="Topic Summary", description="Generate a focused summary about a specific topic from the knowledge base.")
def topic_summary(request: TopicSummaryRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    try:
        chunks = retrieve_context(request.topic, request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    relevant_chunks = [c for c in chunks if c["relevance_score"] > 0.3]

    if not relevant_chunks:
        return {
            "status": "success",
            "topic": request.topic,
            "summary": "No relevant content found for this topic in the uploaded sources.",
            "sources_cited": [],
            "chunks_used": 0
        }

    context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])
    sources_cited = list(set([chunk["source_name"] for chunk in relevant_chunks]))

    try:
        summary = generate_topic_summary(context, request.topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

    return {
        "status": "success",
        "topic": request.topic,
        "summary": summary,
        "sources_cited": sources_cited,
        "chunks_used": len(relevant_chunks)
    }

class PodcastRequest(BaseModel):
    topic: str
    duration: int = 5
    top_k: int = 6

@app.post("/generate-podcast-script", summary="Generate Podcast Script", description="Generate a two-host conversational podcast script on a topic from your knowledge base.")
def generate_podcast_script_endpoint(request: PodcastRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    try:
        chunks = retrieve_context(request.topic, request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # get best score from retrieved chunks
    best_score = max(c["relevance_score"] for c in chunks)

# only reject if even the best chunk is clearly irrelevant
    if best_score < 0.25:
        raise HTTPException(
        status_code=400,
        detail="This topic is not covered in your uploaded sources."
    )

# use all chunks — let the LLM decide what's relevant
    relevant_chunks = chunks

# use all chunks — let the LLM decide what's relevant
    relevant_chunks = chunks
    context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])
    sources_cited = list(set([chunk["source_name"] for chunk in relevant_chunks]))

    try:
        script = generate_podcast_script(context, request.topic, request.duration)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

    return {
    "status": "success",
    "topic": request.topic,
    "duration_minutes": request.duration,
    "sources_cited": sources_cited,
    "disclaimer": "Content generated based on uploaded sources. Verify accuracy for topics not explicitly covered.",
    "script": script
}