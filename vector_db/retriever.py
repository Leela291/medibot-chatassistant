"""
Retrieves the top-K most relevant chunks for a query using FAISS.
"""
import numpy as np
import faiss
import threading

from embeddings.embedding_model import get_embedding
from vector_db.faiss_index import load_index, index_exists
from vector_db.vector_store import build_vector_store
from llm.config import TOP_K_RESULTS


_index = None
_metadata = None
_building = False
_lock = threading.Lock()


def _build_in_background():
    global _building
    try:
        build_vector_store()
        reload_index()
    except Exception as e:
        print(f"[Retriever] Background build failed: {e}")
    finally:
        _building = False


def _ensure_loaded() -> bool:
    global _index, _metadata, _building

    if _index is not None:
        return True

    with _lock:
        if _index is not None:
            return True

        if not index_exists():
            if not _building:
                _building = True
                print("[Retriever] No FAISS index found → building in background...")

                threading.Thread(
                    target=_build_in_background,
                    daemon=True
                ).start()

            return False

        try:
            _index, _metadata = load_index()
            return True

        except Exception as e:
            print(f"[Retriever] Failed to load index: {e}")
            return False


def retrieve(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    """
    Retrieve top-K most relevant chunks.
    """
    if not _ensure_loaded():
        return []

    try:
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

    except Exception as e:
        print(f"[Retriever] Search failed: {e}")
        return []


def reload_index():
    """Force reload FAISS index from disk."""
    global _index, _metadata

    try:
        _index, _metadata = load_index()
    except Exception as e:
        print(f"[Retriever] Reload failed: {e}")
