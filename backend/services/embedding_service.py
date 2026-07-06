# Embedding generation service
# Library: sentence-transformers (all-MiniLM-L6-v2)

from sentence_transformers import SentenceTransformer
import numpy as np

# lazy loading — model loads on first use, not at server startup
# this prevents out-of-memory errors on deployment (Render free tier = 512MB)
_model = None

def get_model():
    """Load and cache the model. Only loads once, reuses on subsequent calls."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def generate_embeddings(chunks: list) -> np.ndarray:
    """
    Convert text chunks into embedding vectors.
    
    Args:
        chunks: list of chunk dictionaries with 'text' key
        
    Returns:
        numpy array of shape (n_chunks, 384)
    """
    # extract just the text from each chunk dictionary
    texts = [chunk["text"] for chunk in chunks]
    
    # generate embeddings for all texts at once
    # show_progress_bar=False for production — no terminal output needed
    embeddings = get_model().encode(texts, show_progress_bar=False)
    
    return embeddings