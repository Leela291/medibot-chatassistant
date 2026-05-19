# embeddings/chunking.py
"""
Converts raw medical JSON documents into overlapping text chunks
suitable for embedding and retrieval.
"""
import json
import os
from pathlib import Path
from llm.config import CHUNK_SIZE, CHUNK_OVERLAP, DATASETS_DIR


def flatten_json(obj: dict | list, prefix: str = "") -> list[str]:
    """Recursively flatten a JSON object into readable sentences."""
    sentences = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            label = key.replace("_", " ").title()
            if isinstance(value, str):
                sentences.append(f"{label}: {value}")
            elif isinstance(value, list):
                sentences.extend(flatten_json(value, prefix=label))
            elif isinstance(value, dict):
                sentences.append(f"--- {label} ---")
                sentences.extend(flatten_json(value, prefix=label))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                sentences.append(f"{prefix}: {item}" if prefix else item)
            elif isinstance(item, dict):
                sentences.extend(flatten_json(item, prefix=prefix))

    return sentences


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split a long text into overlapping word-level chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def load_and_chunk_dataset(json_path: str) -> list[dict]:
    """
    Load a disease JSON file and return a list of chunk dicts:
    {"text": ..., "source": ..., "disease": ...}
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    disease_name = data.get("disease", Path(json_path).stem)
    sentences = flatten_json(data)
    full_text = "\n".join(sentences)

    raw_chunks = chunk_text(full_text)
    return [
        {"text": c, "source": json_path, "disease": disease_name}
        for c in raw_chunks
    ]


def load_all_datasets(datasets_dir: str = DATASETS_DIR) -> list[dict]:
    """Load and chunk all JSON files in the datasets directory."""
    all_chunks = []
    path = Path(datasets_dir)
    if not path.exists():
        raise FileNotFoundError(f"Datasets directory '{datasets_dir}' not found.")

    for json_file in sorted(path.glob("*.json")):
        try:
            chunks = load_and_chunk_dataset(str(json_file))
            all_chunks.extend(chunks)
            print(f"  Loaded {len(chunks)} chunks from {json_file.name}")
        except Exception as e:
            print(f"  [WARNING] Failed to load {json_file.name}: {e}")

    print(f"Total chunks: {len(all_chunks)}")
    return all_chunks
