# vector_db/vector_store.py
"""
Builds (or rebuilds) the FAISS vector store from the disease datasets.
Run directly:  python -m vector_db.vector_store
"""
import numpy as np

from embeddings.chunking import load_all_datasets
from embeddings.embedding_model import get_embeddings_batch
from vector_db.faiss_index import build_index, save_index, index_exists
from llm.config import FAISS_INDEX_PATH


def build_vector_store(force_rebuild: bool = False) -> None:
    if index_exists() and not force_rebuild:
        print("Vector store already exists. Pass force_rebuild=True to rebuild.")
        return

    print("Loading and chunking datasets …")
    chunks = load_all_datasets()

    texts = [c["text"] for c in chunks]

    print(f"Generating embeddings for {len(texts)} chunks …")
    embeddings = get_embeddings_batch(texts)

    print("Building FAISS index …")
    index = build_index(embeddings.copy())   # copy because normalize_L2 is in-place

    save_index(index, chunks)
    print("✅ Vector store built successfully.")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    build_vector_store(force_rebuild=force)
