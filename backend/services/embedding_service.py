# Embedding generation service
# Library: sentence-transformers (all-MiniLM-L6-v2)

from sentence_transformers import SentenceTransformer
import numpy as np

# load model once at module level — not inside the function
# this runs once when the file is first imported
model = SentenceTransformer("all-MiniLM-L6-v2")

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
    embeddings = model.encode(texts, show_progress_bar=True)
    
    return embeddings