"""
Generates embeddings via Ollama's /api/embeddings endpoint.
"""

import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from llm.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL

# Use single worker for stability
MAX_WORKERS = 1

# Safe limit for nomic-embed-text
MAX_WORDS_PER_CHUNK = 220


def get_embedding(text: str) -> np.ndarray:
    """Return a numpy embedding vector for a single text string."""

    # Prevent oversized inputs
    words = text.split()
    if len(words) > MAX_WORDS_PER_CHUNK:
        text = " ".join(words[:MAX_WORDS_PER_CHUNK])

    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text
    }

    try:
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()

        return np.array(
            r.json()["embedding"],
            dtype=np.float32
        )

    except requests.exceptions.HTTPError as e:
        try:
            error_body = r.json()
        except:
            error_body = r.text

        raise RuntimeError(
            f"❌ Ollama Error for model '{OLLAMA_EMBED_MODEL}':\n{error_body}"
        ) from e

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "❌ Cannot connect to Ollama. Run 'ollama serve'"
        )

    except Exception as e:
        raise RuntimeError(
            f"❌ Unexpected embedding error: {e}"
        ) from e


def get_embeddings_batch(
    texts: list[str],
    max_workers: int = MAX_WORKERS
) -> np.ndarray:
    """
    Generate embeddings for a list of texts.
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
            dynamic_ncols=True
        ) as bar:

            for future in as_completed(futures):

                idx = futures[future]

                try:
                    _, emb = future.result()
                    results[idx] = emb

                except Exception as e:

                    tqdm.write(
                        f"[WARNING] chunk {idx} failed: {e}"
                    )

                    existing = next(
                        (r for r in results if r is not None),
                        None
                    )

                    if existing is not None:
                        results[idx] = np.zeros(
                            existing.shape,
                            dtype=np.float32
                        )
                    else:
                        results[idx] = np.zeros(
                            768,
                            dtype=np.float32
                        )

                finally:
                    bar.update(1)

    return np.vstack(results)


def embedding_dimension() -> int:
    """Return embedding dimension."""
    return get_embedding("test").shape[0]