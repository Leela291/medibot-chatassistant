"""
Utility helpers for embedding operations.
"""

import numpy as np
from embeddings.embedding_model import get_embedding


# -----------------------------
# COSINE SIMILARITY
# -----------------------------
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""

    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-10
    return float(np.dot(a, b) / denom)


# -----------------------------
# NORMALIZATION
# -----------------------------
def normalize(vec: np.ndarray) -> np.ndarray:
    """L2-normalize a vector."""

    norm = np.linalg.norm(vec)
    return vec / (norm + 1e-10)


# -----------------------------
# QUERY EMBEDDING
# -----------------------------
def embed_query(query: str) -> np.ndarray:
    """Embed a query string and return normalized vector."""

    vec = get_embedding(query)
    return normalize(vec)
