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


def _chunk_one(obj: dict, source: str) -> list[dict]:
    """Chunk a single disease dict and return list of chunk dicts."""
    disease_name = obj.get("disease", Path(source).stem)
    sentences    = flatten_json(obj)
    full_text    = "\n".join(sentences)
    raw_chunks   = chunk_text(full_text)
    return [
        {"text": c, "source": source, "disease": disease_name}
        for c in raw_chunks
    ]


def load_and_chunk_dataset(json_path: str) -> list[dict]:
    """
    Load a disease JSON file and return a list of chunk dicts:
    {"text": ..., "source": ..., "disease": ...}
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Normalize the root object (handle if it's wrapped in a list)
    if isinstance(data, list) and len(data) > 0:
        primary_obj = data[0]
    elif isinstance(data, dict):
        primary_obj = data
    else:
        primary_obj = {}

    # 2. Robustly extract the disease name across different schemas
    disease_name = None
    
    # Check direct "disease" key
    if "disease" in primary_obj:
        val = primary_obj["disease"]
        if isinstance(val, dict) and "name" in val:  # Handles asthma.json
            disease_name = val["name"]
        elif isinstance(val, str):
            disease_name = val
            
    # Check "summary_profile" nesting (from our previous fix)
    elif "summary_profile" in primary_obj and "disease" in primary_obj["summary_profile"]:
        disease_name = primary_obj["summary_profile"]["disease"]
        
    # Check "disease_identity" nesting
    elif "disease_identity" in primary_obj and "name" in primary_obj["disease_identity"]:
        disease_name = primary_obj["disease_identity"]["name"]

    # Fallback to the filename if the key is missing entirely
    disease_name = disease_name or Path(json_path).stem

    # 3. Flatten and chunk as normal
    sentences = flatten_json(data)
    full_text = "\n".join(sentences)

    raw_chunks = chunk_text(full_text)
    return [
        {"text": c, "source": json_path, "disease": disease_name}
        for c in raw_chunks
    ]

    # ── chunk every disease object and combine ────────────────────────
    all_chunks = []
    for obj in items:
        all_chunks.extend(_chunk_one(obj, json_path))

    return all_chunks


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
