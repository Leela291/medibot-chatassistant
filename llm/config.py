import os
from dotenv import load_dotenv

load_dotenv()

# ── Ollama settings ─────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

# Better model for medical reasoning
OLLAMA_LLM_MODEL = os.getenv(
    "OLLAMA_LLM_MODEL",
    "llama3.2:1b"
)

# Embedding model
OLLAMA_EMBED_MODEL = os.getenv(
    "OLLAMA_EMBED_MODEL",
    "nomic-embed-text"
)

# ── API settings ────────────────────────────────────────────────────────────
OPENFDA_API_KEY = os.getenv("OPENFDA_API_KEY", "")

# ── RAG settings ────────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 256))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 64))

# Increased retrieval depth
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 5))

# ── FAISS settings ──────────────────────────────────────────────────────────
FAISS_INDEX_PATH = os.getenv(
    "FAISS_INDEX_PATH",
    "vector_db/db/faiss.index"
)

METADATA_PATH = os.getenv(
    "METADATA_PATH",
    "vector_db/db/metadata.pkl"
)

# ── Dataset path ────────────────────────────────────────────────────────────
DATASETS_DIR = os.getenv(
    "DATASETS_DIR",
    "datasets"
)

# ── Session / Memory ────────────────────────────────────────────────────────
MAX_HISTORY_TURNS = int(
    os.getenv("MAX_HISTORY_TURNS", 3)
)

# ── Generation parameters ───────────────────────────────────────────────────
LLM_TEMPERATURE = float(
    os.getenv("LLM_TEMPERATURE", 0.3)
)

LLM_MAX_TOKENS = int(
    os.getenv("LLM_MAX_TOKENS", 512)
)
