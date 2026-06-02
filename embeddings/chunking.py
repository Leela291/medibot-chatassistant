# embeddings/chunking.py
"""
Converts raw medical JSON documents into overlapping text chunks
suitable for embedding and retrieval.
"""

import json
from pathlib import Path
from llm.config import CHUNK_SIZE, CHUNK_OVERLAP, DATASETS_DIR


# -----------------------------
# JSON FLATTENING
# -----------------------------
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


# -----------------------------
# CHUNKING LOGIC
# -----------------------------
def chunk_text(text: str,
               chunk_size: int = CHUNK_SIZE,
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


# -----------------------------
# DISEASE NAME NORMALIZATION
# -----------------------------
def _canonical_disease_name(json_path: str) -> str:
    """Map dataset filename to a stable disease label used in retrieval."""
    stem = Path(json_path).stem

    aliases = {
        "commoncold": "Common Cold",
        "covid19": "COVID-19",
    }

    key = stem.lower().replace("_", "")
    return aliases.get(key) or stem.replace("_", " ").title()


# -----------------------------
# SINGLE FILE PROCESSING
# -----------------------------
def load_and_chunk_dataset(json_path: str) -> list[dict]:
    """
    Load a disease JSON file and return list of chunk dicts:
    {
        "text": ...,
        "source": ...,
        "disease": ...
    }
    """

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    disease_name = _canonical_disease_name(json_path)

    sentences = flatten_json(data)
    full_text = "\n".join(sentences)

    raw_chunks = chunk_text(full_text)

    return [
        {
            "text": chunk,
            "source": json_path,
            "disease": disease_name
        }
        for chunk in raw_chunks
    ]


# -----------------------------
# LOAD ALL DATASETS
# -----------------------------
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
            print(f"Loaded {len(chunks)} chunks from {json_file.name}")

        except Exception as e:
            print(f"[WARNING] Failed to load {json_file.name}: {e}")

    print(f"Total chunks: {len(all_chunks)}")

    return all_chunks
