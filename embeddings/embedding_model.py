# embeddings/embedding_model.py
"""
Generates embeddings via Ollama's /api/embeddings endpoint.
"""
import requests
import numpy as np
from llm.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL


def get_embedding(text: str) -> np.ndarray:
    """Return a numpy embedding vector for a single text string."""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": OLLAMA_EMBED_MODEL, "prompt": text}

    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        return np.array(r.json()["embedding"], dtype=np.float32)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama server not reachable. Run `ollama serve`.")
    except KeyError:
        raise RuntimeError(f"Model '{OLLAMA_EMBED_MODEL}' may not support embeddings. "
                           f"Run `ollama pull {OLLAMA_EMBED_MODEL}`.")


def get_embeddings_batch(texts: list[str]) -> np.ndarray:
    """Return a 2-D numpy array of embeddings for a list of texts."""
    embeddings = [get_embedding(t) for t in texts]
    return np.vstack(embeddings)


def embedding_dimension() -> int:
    """Return the dimension of the embedding model (probe with a dummy text)."""
    return get_embedding("test").shape[0]
