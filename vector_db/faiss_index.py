"""
Manages the FAISS index — creation, saving, and loading.
"""
import os
import pickle
import numpy as np
import faiss

from llm.config import FAISS_INDEX_PATH, METADATA_PATH


def build_index(embeddings: np.ndarray) -> faiss.Index:
    """Build an inner-product (cosine after L2-normalization) FAISS index."""
    dim = embeddings.shape[1]

    # Normalize embeddings BEFORE adding
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    return index


def save_index(
    index: faiss.Index,
    metadata: list[dict],
    index_path: str = FAISS_INDEX_PATH,
    meta_path: str = METADATA_PATH
) -> None:
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    faiss.write_index(index, index_path)

    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)

    print(f"Index saved → {index_path} ({index.ntotal} vectors)")


def load_index(
    index_path: str = FAISS_INDEX_PATH,
    meta_path: str = METADATA_PATH
) -> tuple[faiss.Index, list[dict]]:

    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"FAISS index not found at '{index_path}'. "
            "Run vector store build first."
        )

    index = faiss.read_index(index_path)

    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    print(f"Index loaded ← {index_path} ({index.ntotal} vectors)")

    return index, metadata


def index_exists(index_path: str = FAISS_INDEX_PATH) -> bool:
    return os.path.exists(index_path)
