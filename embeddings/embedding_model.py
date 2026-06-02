"""
Generates embeddings via Ollama's /api/embeddings endpoint,
with optional batching, safe fallbacks, and robust error handling.
"""

import os
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from llm.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL


# -----------------------------
# CONFIG
# -----------------------------
MAX_WORKERS = 4
MAX_WORDS_PER_CHUNK = 220


# -----------------------------
# SINGLE EMBEDDING
# -----------------------------
def get_embedding(text: str) -> np.ndarray:
    """Return embedding vector for a single text string."""

    # Ensure GEMINI key is optional (future fallback support)
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_key = gemini_key if gemini_key and gemini_key.strip() else None

    # Prevent oversized input (important for Ollama stability)
    words = text.split()
    if len(words) > MAX_WORDS_PER_CHUNK:
        text = " ".join(words[:MAX_WORDS_PER_CHUNK])

    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text
    }

    try:
        # ---------------- Ollama primary ----------------
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()

        return np.array(
            r.json()["embedding"],
            dtype=np.float32
        )

    except Exception as ollama_err:

        # ---------------- Gemini fallback ----------------
        if gemini_key:
            try:
                gemini_url = (
                    "https://generativelanguage.googleapis.com/v1beta/"
                    f"models/text-embedding-004:embedContent?key={gemini_key}"
                )

                gemini_payload = {
                    "model": "models/text-embedding-004",
                    "content": {
                        "parts": [{"text": text}]
                    }
                }

                r = requests.post(gemini_url, json=gemini_payload, timeout=30)
                r.raise_for_status()

                embedding_vals = r.json()["embedding"]["values"]

                return np.array(embedding_vals, dtype=np.float32)

            except Exception as gemini_err:
                raise RuntimeError(
                    "❌ Embedding failed completely.\n"
                    f"Ollama error: {ollama_err}\n"
                    f"Gemini fallback error: {gemini_err}"
                ) from gemini_err

        # No fallback available
        raise RuntimeError(
            "❌ Cannot connect to Ollama and no valid GEMINI_API_KEY found.\n"
            f"Ollama error: {ollama_err}"
        ) from ollama_err


# -----------------------------
# BATCH EMBEDDING
# -----------------------------
def get_embeddings_batch(
    texts: list[str],
    max_workers: int = MAX_WORKERS
) -> np.ndarray:
    """
    Generate embeddings for a list of texts in parallel.
    Preserves order and prevents crashes with fallback zero vectors.
    """

    total = len(texts)
    results = [None] * total

    def _embed(idx_text):
        idx, text = idx_text
        return idx, get_embedding(text)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:

        futures = {
            pool.submit(_embed, (i, text)): i
            for i, text in enumerate(texts)
        }

        with tqdm(
            total=total,
            desc="Embedding chunks",
            unit="chunk",
            dynamic_ncols=True,
            colour="cyan"
        ) as bar:

            for future in as_completed(futures):
                idx = futures[future]

                try:
                    i, emb = future.result()
                    results[i] = emb

                except Exception as e:
                    tqdm.write(f"[WARNING] chunk {idx} failed: {e}")

                    # fallback safe vector
                    existing = next((r for r in results if r is not None), None)

                    dim = existing.shape[0] if existing is not None else 768
                    results[idx] = np.zeros(dim, dtype=np.float32)

                finally:
                    bar.update(1)

    return np.vstack(results)


# -----------------------------
# UTILITY
# -----------------------------
def embedding_dimension() -> int:
    """Return embedding dimension of the model."""
    return get_embedding("test").shape[0]
