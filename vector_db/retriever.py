# vector_db/retriever.py
"""
Retrieves the top-K most relevant chunks for a query using FAISS.
"""
import numpy as np
import faiss

from embeddings.embedding_model import get_embedding
from vector_db.faiss_index import load_index, index_exists, build_index, save_index
from vector_db.vector_store import build_vector_store
from llm.config import TOP_K_RESULTS

_index = None
_metadata = None

def _ensure_loaded():
    global _index, _metadata
    if _index is None:
        if not index_exists():
            print("Vector store not found — building now …")
            build_vector_store()
        _index, _metadata = load_index()


def retrieve(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    """
    Retrieve the top_k most relevant chunks for a query.

    Returns a list of dicts: {"text": ..., "source": ..., "disease": ..., "score": ...}
    """
    _ensure_loaded()

    query_vec = get_embedding(query).reshape(1, -1).astype(np.float32)
    faiss.normalize_L2(query_vec)

    scores, indices = _index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = _metadata[idx].copy()
        chunk["score"] = float(score)
        results.append(chunk)

    return results

def reload_index():
    """Force-reload the FAISS index from disk."""
    global _index, _metadata
    _index, _metadata = load_index()
