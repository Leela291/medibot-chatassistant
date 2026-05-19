# embeddings/embedding_utils.py
"""Utility helpers for embedding operations."""
import numpy as np
from embeddings.embedding_model import get_embedding


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def normalize(vec: np.ndarray) -> np.ndarray:
    """L2-normalize a vector."""
    norm = np.linalg.norm(vec)
    return vec / (norm + 1e-10)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string and normalize it."""
    vec = get_embedding(query)
    return normalize(vec)
