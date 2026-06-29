#KnowledgeCast AI - Backend
from fastapi import FastAPI,File,Form,UploadFile,HTTPException
import os
import shutil
from datetime import datetime
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.url_service import extract_text_from_url
from typing import List, Optional
from backend.services.chunk_service import chunk_sources
from backend.services.embedding_service import generate_embeddings
from backend.services.rag_service import build_knowledge_base, retrieve_context
from pydantic import BaseModel
from backend.services.llm_service import generate_answer, generate_summary

app = FastAPI()

@app.get("/")
def home():
    return {"message": "KnowledgeCast AI is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}








@app.get("/About")
def home():
    return {"project": "KnowledgeCast AI"}



class gr(BaseModel):
    name:str

@app.post("/generate_name")

def generate_name(request:gr):
    return {"message": f"Hello{request.name}"}

from pydantic import BaseModel

class ge(BaseModel):
    topic:str

@app.post("/topic_details")
def topic_details(request:ge):
    return {"received topic":request.topic}


@app.get("/user/{user_id}")

def get_id(user_id:int):
    return{"user_id":user_id, "message":"user found"}

@app.get("/search")
def search_topic(topic: str, limit: int = 5):
    return {"topic": topic, "limit": limit}
    

@app.post("/upload-pdf")
def upload_pdf(file: UploadFile = File(...)):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    upload_folder = "data/uploads"
    os.makedirs(upload_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"

    file_path = os.path.join(upload_folder, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
     
    return {
        "original_filename": file.filename,
        "saved_filename": safe_filename,
        "content_type": file.content_type,
        "file_path": file_path,
        "message": "File received successfully"
    }

@app.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    # check if uploaded file is actually a PDF
    if not file.filename.endswith(".pdf"):
        return {"error": "only PDF files are allowed"}
    
    # save uploaded file to uploads folder
    save_path = f"uploads/{file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # extract text using our pdf_service
    text = extract_text_from_pdf(save_path)
    
    # return first 1000 characters as preview
    return {
        "filename": file.filename,
        "status": "extracted successfully",
        "character_count": len(text),
        "preview": text[:1000]
    }

class URLRequest(BaseModel):
    url: str

@app.post("/extract-url")
def extract_url(request: URLRequest):
    try:
        result = extract_text_from_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "title": result["title"],
        "status": "extracted successfully",
        "character_count": len(result["text"]),
        "preview": result["text"][:1000]
    }


@app.post("/process-sources")
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
            failed_sources.append({
                "source": file.filename,
                "error": "only PDF files are allowed"
            })
            continue

        save_path = f"uploads/{file.filename}"
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            text = extract_text_from_pdf(save_path)
            sources.append({
                "source_name": file.filename,
                "source_type": "pdf",
                "text": text
            })
        except Exception as e:
            failed_sources.append({
                "source": file.filename,
                "error": str(e)
            })

    # step 2 — extract text from URLs
    if urls_input.strip():
        urls = [url.strip() for url in urls_input.split(",")]
        for url in urls:
            if not url:
                continue
            try:
                result = extract_text_from_url(url)
                sources.append({
                    "source_name": url,
                    "source_type": "url",
                    "text": result["text"]
                })
            except Exception as e:
                failed_sources.append({
                    "source": url,
                    "error": str(e)
                })

    # check if anything succeeded
    if not sources:
        raise HTTPException(
            status_code=400,
            detail="No sources could be processed successfully."
        )

    # step 3 — chunk all sources
    try:
        chunks = chunk_sources(sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunking failed: {str(e)}")

    # step 4 — generate embeddings
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


@app.post("/test-chunking")
async def test_chunking(
    files: List[UploadFile] = File(default=None),
    urls_input: str = Form(default="")
):
    if files is None:
        files = []

    sources = []

    # process PDFs
    for file in files:
        if not file.filename.endswith(".pdf"):
            continue
        save_path = f"uploads/{file.filename}"
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        try:
            text = extract_text_from_pdf(save_path)
            sources.append({
                "source_name": file.filename,
                "source_type": "pdf",
                "text": text
            })
        except Exception as e:
            continue

    # process URLs
    if urls_input.strip():
        urls = [url.strip() for url in urls_input.split(",")]
        for url in urls:
            if not url:
                continue
            try:
                result = extract_text_from_url(url)
                sources.append({
                    "source_name": url,
                    "source_type": "url",
                    "text": result["text"]
                })
            except Exception as e:
                continue

    if not sources:
        raise HTTPException(status_code=400, detail="No sources could be processed.")

    # chunk all sources
    chunks = chunk_sources(sources)

    # return summary — not all chunks, just stats
    return {
        "total_sources": len(sources),
        "total_chunks": len(chunks),
        "average_chunk_length": sum(len(c["text"]) for c in chunks) // len(chunks),
        "sample_chunk": chunks[0],
        "sample_chunk_2": chunks[1] if len(chunks) > 1 else None
    }

@app.post("/test-embeddings")
async def test_embeddings(file: UploadFile = File(...)):
    # save file
    save_path = f"uploads/{file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # extract text
    try:
        text = extract_text_from_pdf(save_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # chunk it
    sources = [{"source_name": file.filename, "source_type": "pdf", "text": text}]
    chunks = chunk_sources(sources)

    # generate embeddings
    embeddings = generate_embeddings(chunks)

    return {
        "total_chunks": len(chunks),
        "embedding_shape": list(embeddings.shape),
        "first_embedding_sample": embeddings[0][:10].tolist(),
        "embedding_dimensions": embeddings.shape[1]
    }

@app.post("/build-knowledge-base")
async def build_kb(file: UploadFile = File(...)):
    # save file
    save_path = f"uploads/{file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # extract text
    try:
        text = extract_text_from_pdf(save_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # chunk
    sources = [{"source_name": file.filename, "source_type": "pdf", "text": text}]
    chunks = chunk_sources(sources)

    # embed
    embeddings = generate_embeddings(chunks)

    # build FAISS index
    result = build_knowledge_base(chunks, embeddings)

    return {
        "status": "knowledge base built successfully",
        "total_chunks": result["total_vectors"],
        "dimensions": result["dimensions"],
        "index_saved_at": result["index_saved"],
        "chunks_saved_at": result["chunks_saved"]
    }


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/retrieve-context")
def retrieve(request: QueryRequest):
    try:
        chunks = retrieve_context(request.query, request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "query": request.query,
        "top_k": request.top_k,
        "results": chunks
    }

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/ask")
def ask(request: QueryRequest):
    try:
        chunks = retrieve_context(request.query, request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # combine retrieved chunks into one context string
    context = "\n\n".join([chunk["text"] for chunk in chunks])

    # list unique sources used
    sources_cited = list(set([chunk["source_name"] for chunk in chunks]))

    # call LLM with context and query
    try:
        answer = generate_answer(request.query, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    return {
        "query": request.query,
        "answer": answer,
        "sources_cited": sources_cited,
        "chunks_retrieved": len(chunks)
    }

class SummaryRequest(BaseModel):
    topic: str = ""

@app.post("/generate-summary")
def generate_summary_endpoint(request: SummaryRequest):
    # retrieve relevant context
    try:
        if request.topic.strip():
            chunks = retrieve_context(request.topic, top_k=8)
        else:
            # if no topic, load all chunks
            import json
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
        "topic": request.topic if request.topic else "full knowledge base",
        "summary": summary
    }

