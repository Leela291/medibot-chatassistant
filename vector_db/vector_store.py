"""
Builds (or rebuilds) the FAISS vector store from disease datasets.
Supports incremental updates using hashing.
"""
import hashlib
import faiss

from embeddings.chunking import load_all_datasets
from embeddings.embedding_model import get_embeddings_batch
from vector_db.faiss_index import (
    build_index, save_index, load_index, index_exists
)


def _hash_chunk(text: str) -> str:
    """Stable hash for deduplication."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def build_vector_store(force_rebuild: bool = False) -> None:
    print("Loading datasets...")
    all_chunks = load_all_datasets()
    print(f"Total chunks: {len(all_chunks)}")

    # ───────────────────────────────
    # Force rebuild
    # ───────────────────────────────
    if force_rebuild:
        print("Force rebuild enabled")
        return _build_fresh(all_chunks)

    # ───────────────────────────────
    # No index → fresh build
    # ───────────────────────────────
    if not index_exists():
        print("No FAISS index found → building fresh")
        return _build_fresh(all_chunks)

    # ───────────────────────────────
    # Incremental update
    # ───────────────────────────────
    print("Loading existing index...")

    existing_index, existing_metadata = load_index()

    existing_hashes = set()

    for m in existing_metadata:
        text = m.get("text")
        if text:
            existing_hashes.add(_hash_chunk(text))

    new_chunks = [
        c for c in all_chunks
        if _hash_chunk(c["text"]) not in existing_hashes
    ]

    if not new_chunks:
        print(f"Index already up-to-date ({len(existing_metadata)} chunks)")
        return

    print(f"New chunks found: {len(new_chunks)}")

    new_texts = [c["text"] for c in new_chunks]
    new_embeddings = get_embeddings_batch(new_texts)

    faiss.normalize_L2(new_embeddings)

    existing_index.add(new_embeddings)

    updated_metadata = existing_metadata + new_chunks

    save_index(existing_index, updated_metadata)

    print(f"Updated index: {len(updated_metadata)} total chunks")


def _build_fresh(chunks: list[dict]) -> None:
    texts = [c["text"] for c in chunks]

    print(f"Embedding {len(texts)} chunks...")

    embeddings = get_embeddings_batch(texts)

    index = build_index(embeddings.copy())

    save_index(index, chunks)

    print("Vector store built successfully")


if __name__ == "__main__":
    import sys
    build_vector_store(force_rebuild="--force" in sys.argv)
