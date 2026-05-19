# llm/model_loader.py
"""
Thin wrapper that verifies the Ollama server is reachable and the
requested model is available locally.
"""
import requests
from llm.config import OLLAMA_BASE_URL, OLLAMA_LLM_MODEL, OLLAMA_EMBED_MODEL


def check_ollama_connection() -> bool:
    """Return True if Ollama server is running."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def list_local_models() -> list[str]:
    """Return list of model names available on the local Ollama server."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def ensure_model(model_name: str) -> bool:
    """Check if a model is available; print hint if not."""
    local = list_local_models()
    available = any(model_name in m for m in local)
    if not available:
        print(f"[WARNING] Model '{model_name}' not found locally.")
        print(f"          Run:  ollama pull {model_name}")
    return available


def get_model_info() -> dict:
    return {
        "llm_model":   OLLAMA_LLM_MODEL,
        "embed_model": OLLAMA_EMBED_MODEL,
        "base_url":    OLLAMA_BASE_URL,
        "connected":   check_ollama_connection(),
        "local_models": list_local_models(),
    }
