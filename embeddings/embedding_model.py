# embeddings/embedding_model.py
"""
Generates embeddings via Ollama's /api/embeddings endpoint, 
with a fallback to the Gemini API if local connection fails.
"""
import requests
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from llm.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL

# 8 is safe for local Ollama; raise to 16 if your machine has more RAM
MAX_WORKERS = 4

def get_embedding(text: str) -> np.ndarray:
    """Return a numpy embedding vector for a single text string."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key.strip() == "":
        gemini_key = None

    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": OLLAMA_EMBED_MODEL, "prompt": text}

    try:
        # Try Ollama first (with a reasonable timeout)
        r = requests.post(url, json=payload, timeout=90)
        r.raise_for_status()
        return np.array(r.json()["embedding"], dtype=np.float32)
    
    except Exception as ollama_err:
        # If Ollama fails, attempt the Gemini Fallback
        if gemini_key:
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={gemini_key}"
                gemini_payload = {
                    "model": "models/text-embedding-004",
                    "content": {
                        "parts": [{"text": text}]
                    }
                }
                r = requests.post(gemini_url, json=gemini_payload, timeout=20)
                r.raise_for_status()
                embedding_vals = r.json()["embedding"]["values"]
                return np.array(embedding_vals, dtype=np.float32)
            except Exception as gemini_err:
                raise RuntimeError(
                    f"❌ Embedding failed.\nOllama error: {ollama_err}\n"
                    f"Gemini fallback error: {gemini_err}"
                ) from gemini_err
        else:
            raise RuntimeError(
                f"❌ Cannot connect to Ollama and no valid GEMINI_API_KEY found.\n"
                f"Ollama error: {ollama_err}"
            ) from ollama_err

def get_embeddings_batch(texts: list[str],
                         max_workers: int = MAX_WORKERS) -> np.ndarray:
    """
    Return a 2-D numpy array of embeddings for a list of texts.
    Fires up to `max_workers` requests in parallel.
    """
    total   = len(texts)
    results = [None] * total          # pre-allocate to keep original order

    def _embed(idx_text: tuple[int, str]) -> tuple[int, np.ndarray]:
        idx, text = idx_text
        return idx, get_embedding(text)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_embed, (i, t)): i
            for i, t in enumerate(texts)
        }

        with tqdm(total=total,
                  desc="  Embedding chunks",
                  unit="chunk",
                  dynamic_ncols=True,
                  colour="cyan") as bar:

            for future in as_completed(futures):
                try:
                    idx, emb = future.result()
                    results[idx] = emb
                except Exception as e:
                    idx = futures[future]
                    # On error, create a zero vector to prevent vstack crashes
                    existing = next((r for r in results if r is not None), None)
                    
                    # Assume dimension is 768 for both Ollama/Gemini if no existing vectors
                    dim = existing.shape[0] if existing is not None else 768 
                    results[idx] = np.zeros(dim, dtype=np.float32)
                    
                    tqdm.write(f"  [WARNING] chunk {idx} failed: {e}")
                finally:
                    bar.update(1)

    return np.vstack(results)

def embedding_dimension() -> int:
    """Return the dimension of the embedding model."""
    return get_embedding("test").shape[0]