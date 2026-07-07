# RAG retrieval service
# Library: FAISS + sentence-transformers

import faiss
import numpy as np
import json
import os
from backend.services.embedding_service import get_model

# paths where we save index and chunks
INDEX_PATH = "/tmp/index.faiss"
CHUNKS_PATH = "/tmp/chunks.json"


def build_knowledge_base(chunks: list, embeddings: np.ndarray) -> dict:
    """
    Build FAISS index from chunks and embeddings, save to disk.
    
    Args:
        chunks: list of chunk dictionaries with text and metadata
        embeddings: numpy array of shape (n_chunks, 384)
        
    Returns:
        dictionary with build stats
    """
    # get embedding dimensions from the array shape
    dimension = embeddings.shape[1]

    # create FAISS index
    index = faiss.IndexFlatL2(dimension)

    # convert to float32 — FAISS requires float32, not float64
    embeddings_float32 = embeddings.astype(np.float32)

    # add all embeddings to the index
    index.add(embeddings_float32)

    # save FAISS index to disk
    faiss.write_index(index, INDEX_PATH)

    # save chunks to disk as JSON — needed to retrieve text later
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    return {
        "total_vectors": index.ntotal,
        "dimensions": dimension,
        "index_saved": INDEX_PATH,
        "chunks_saved": CHUNKS_PATH
    }


def retrieve_context(query: str, top_k: int = 5) -> list:
    """
    Search FAISS index for most relevant chunks to a query.
    
    Args:
        query: the question or topic to search for
        top_k: number of most relevant chunks to return
        
    Returns:
        list of most relevant chunk dictionaries
    """
    # check index exists
    if not os.path.exists(INDEX_PATH):
        raise ValueError("No knowledge base found. Please process sources first.")

    # load FAISS index from disk
    index = faiss.read_index(INDEX_PATH)

    # load chunks from disk
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # convert query to embedding vector
    query_embedding = get_model().encode([query])
    query_embedding = query_embedding.astype(np.float32)

    # search FAISS index
    distances, indices = index.search(query_embedding, top_k)

    # retrieve actual chunks using returned indices
    relevant_chunks = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks):
            chunk = chunks[idx].copy()
            chunk["relevance_score"] = float(1 / (1 + distances[0][i]))
            relevant_chunks.append(chunk)

    return relevant_chunks