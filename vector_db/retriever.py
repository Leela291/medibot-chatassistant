"""
Retrieves the top-K most relevant chunks for a query using FAISS.
Includes a Hybrid Search to bypass FAISS for exact disease matches.
"""
import numpy as np
import faiss
import json
import os
import glob

from embeddings.embedding_model import get_embedding
from vector_db.faiss_index import load_index, index_exists, build_index, save_index
from vector_db.vector_store import build_vector_store
from llm.config import TOP_K_RESULTS

_index = None
_metadata = None

# --- UPDATED: Load ALL individual JSON files from the datasets folder ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")

DISEASE_DB = []
if os.path.exists(DATASETS_DIR):
    # Scan the directory for every .json file
    for filepath in glob.glob(os.path.join(DATASETS_DIR, "*.json")):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Safely add the data whether it's a list of diseases or just one
                if isinstance(data, list):
                    DISEASE_DB.extend(data)
                elif isinstance(data, dict):
                    DISEASE_DB.append(data)
            except json.JSONDecodeError:
                print(f"Warning: Could not read JSON from {filepath}")

def _ensure_loaded():
    global _index, _metadata
    if _index is None:
        if not index_exists():
            print("Vector store not found — building now …")
            build_vector_store()
        _index, _metadata = load_index()


def retrieve(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    """
    Retrieve the top_k most relevant chunks for a query.
    Uses Hybrid Search: Checks for exact disease names first, then falls back to FAISS.
    """
    query_lower = query.lower()
    
    # 1. KEYWORD MATCH (The exact match bypass)
    for entry in DISEASE_DB:
        # Safely handle the disease name in case the LLM nested it inside a dictionary
        raw_disease = entry.get("disease", "")
        if isinstance(raw_disease, dict):
            disease_name = str(raw_disease.get("name", "")).lower()
        else:
            disease_name = str(raw_disease).lower()

        # Ensure aliases is actually a list of strings to prevent crashes
        raw_aliases = entry.get("aliases", [])
        aliases = []
        if isinstance(raw_aliases, list):
            aliases = [str(a).lower() for a in raw_aliases if isinstance(a, str)]

        # If we couldn't find a valid name in this file, skip it safely
        if not disease_name:
            continue
            
        # If the user directly asks about "Common Cold" or an alias like "Cold"
        if disease_name in query_lower or any(alias in query_lower for alias in aliases):
            print(f"  -> Exact match found for: {disease_name.title()} (Bypassing FAISS)")
            
            # Helper function to safely join arrays even if the LLM messed up the format
            def safe_join(field):
                val = entry.get(field, [])
                return ", ".join([str(v) for v in val]) if isinstance(val, list) else str(val)

            # Format the JSON data nicely into text for the LLM
            context = f"Disease: {disease_name.title()}\n"
            context += f"Description: {entry.get('description', '')}\n"
            context += f"Symptoms: {safe_join('common_symptoms')}\n"
            context += f"Treatments: {safe_join('treatment_options')}\n"
            context += f"Home Remedies: {safe_join('lifestyle_home_remedies')}\n"
            context += f"Diet: {safe_join('preferred_foods')}\n"
            context += f"Avoid: {safe_join('foods_to_avoid')}\n"
            context += f"When to see a doctor: {entry.get('when_to_see_doctor', '')}\n"
            
            # Disguise the exact match as a standard vector search result
            return [{
                "text": context,
                "source": "MediBot Verified Database",
                "disease": disease_name.title(),
                "score": 1.0 
            }]

    # 2. VECTOR SEARCH FALLBACK
    print("  -> No exact disease match found, running FAISS Vector Search...")
    _ensure_loaded()

    query_vec = get_embedding(query).reshape(1, -1).astype(np.float32)
    faiss.normalize_L2(query_vec)

    scores, indices = _index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = _metadata[idx].copy()
        chunk["score"] = float(score)
        results.append(chunk)

    return results

def reload_index():
    """Force-reload the FAISS index from disk."""
    global _index, _metadata
    _index, _metadata = load_index()
