# vector_db/vector_store.py
"""
Builds (or rebuilds) the FAISS vector store from the disease datasets.
Incremental mode (default):
  - Hashes every chunk by its text content
  - Skips chunks already present in the existing index
  - Only embeds + adds genuinely new chunks
  - Rebuilds from scratch only when --force is passed
Run directly:
  python -m vector_db.vector_store          # incremental (fast)
  python -m vector_db.vector_store --force  # full rebuild
"""
import hashlib
import numpy as np

from embeddings.chunking import load_all_datasets
from embeddings.embedding_model import get_embeddings_batch
from vector_db.faiss_index import (
    build_index, save_index, load_index, index_exists
)
from llm.config import FAISS_INDEX_PATH

def _hash_chunk(text: str) -> str:
    """Stable MD5 hash used as a unique ID for each chunk."""
    return hashlib.md5(text.encode()).hexdigest()


def build_vector_store(force_rebuild: bool = False) -> None:
    # ── 1. Load all chunks from JSON datasets ────────────────────────
    print("Loading and chunking datasets …")
    all_chunks = load_all_datasets()
    print(f"Total chunks from datasets: {len(all_chunks)}")

    # ── 2. Force rebuild — wipe and start fresh ──────────────────────
    if force_rebuild:
        print("Force rebuild — re-embedding all chunks …")
        _build_fresh(all_chunks)
        return

    # ── 3. No existing index — build from scratch ────────────────────
    if not index_exists():
        print("No existing index found — building from scratch …")
        _build_fresh(all_chunks)
        return

    # ── 4. Incremental update ─────────────────────────────────────────
    print("Existing index found — checking for new chunks …")
    existing_index, existing_metadata = load_index()

    # hash every chunk already in the index
    existing_hashes = {
        _hash_chunk(m["text"])
        for m in existing_metadata
        if "text" in m
    }

    # find chunks NOT yet in the index
    new_chunks = [
        c for c in all_chunks
        if _hash_chunk(c["text"]) not in existing_hashes
    ]

    if not new_chunks:
        print(f"✅ Index is already up to date — {len(existing_metadata)} chunks, nothing to add.")
        return

    print(f"  Already indexed : {len(existing_metadata)} chunks  (skipping)")
    print(f"  New chunks found: {len(new_chunks)}  (embedding now …)")

    # embed only the new chunks
    new_texts      = [c["text"] for c in new_chunks]
    new_embeddings = get_embeddings_batch(new_texts)          # uses cache too
    import faiss
    faiss.normalize_L2(new_embeddings)

    # add to the existing index
    existing_index.add(new_embeddings)
    updated_metadata = existing_metadata + new_chunks

    save_index(existing_index, updated_metadata)
    print(f"✅ Index updated — {len(updated_metadata)} total chunks "
          f"({len(new_chunks)} new added).")


def _build_fresh(chunks: list[dict]) -> None:
    """Embed all chunks and build a brand-new FAISS index."""
    texts      = [c["text"] for c in chunks]
    print(f"Generating embeddings for {len(texts)} chunks …")
    embeddings = get_embeddings_batch(texts)

    print("Building FAISS index …")
    index = build_index(embeddings.copy())   # copy — normalize_L2 is in-place
    save_index(index, chunks)
    print("✅ Vector store built successfully.")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    build_vector_store(force_rebuild=force)
