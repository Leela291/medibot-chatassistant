# 🏥 MediBot — AI Medical Chatbot

An AI-powered medical chatbot that provides health information about **Asthma**, **Dengue**, **Diabetes**, and **Hyperthyroidism**. Built with **Flask + React + Ollama (LLaMA 3.2)** using RAG (Retrieval Augmented Generation).

![MediBot](https://img.shields.io/badge/MediBot-AI%20Medical%20Assistant-00d2ff?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![Ollama](https://img.shields.io/badge/Ollama-LLaMA%203.2-FF6B6B?style=flat-square)

---

## ✨ Features

- 💬 **Medical Q&A** — Ask about symptoms, treatments, causes, prevention
- 🔍 **RAG Pipeline** — Uses FAISS vector search for accurate medical answers
- 📎 **Patient Record Upload** — Upload PDF, images, CSV, Excel for AI analysis
- 🚨 **Emergency Detection** — Auto-detects emergency symptoms
- 🩺 **Doctor Search** — Find doctors by condition/city
- 📅 **Appointment Booking** — Book appointments with available slots
- 🧠 **Session Memory** — Remembers conversation context
- 🎨 **Premium Dark UI** — Modern medical-themed interface

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, CSS3 (Dark Mode) |
| **Backend** | Flask, Flask-CORS |
| **AI Model** | Ollama + LLaMA 3.2 (local) |
| **Embeddings** | nomic-embed-text |
| **Vector DB** | FAISS |
| **File Parsing** | PyPDF2, Pillow, openpyxl |

---

## 🚀 Setup Instructions

### Prerequisites

Install these first:
- [Python 3.11+](https://python.org/downloads) — ⚠️ Check "Add to PATH" during install
- [Node.js 18+](https://nodejs.org)
- [Ollama](https://ollama.com/download)

### Step 1 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/medibot-chatbot.git
cd medibot-chatbot
```

### Step 2 — Pull AI models (run once, takes 5-10 min)

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Step 3 — Setup Python backend

```bash
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 4 — Create `.env` file

Create a file named `.env` in the root folder with:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K_RESULTS=5
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1024
MAX_HISTORY_TURNS=10
```

### Step 5 — Build vector database (run once)

```bash
python -m vector_db.vector_store
```

### Step 6 — Start everything (3 terminals)

**Terminal 1 — Ollama:**
```bash
ollama serve
```

**Terminal 2 — Backend:**
```bash
venv\Scripts\activate
python backend/app.py
```
→ Running on http://localhost:5000

**Terminal 3 — Frontend:**
```bash
cd frontend
npm install    # first time only
npm start
```
→ Opens at http://localhost:3000

---

## 📁 Project Structure

```
chatbot/
├── backend/
│   ├── app.py              # Flask entry point
│   ├── routes.py            # Route registration
│   ├── chatbot_api.py       # Chat, upload, doctor, appointment APIs
│   └── file_parser.py       # PDF, image, CSV, Excel parser
├── datasets/
│   ├── asthma.json
│   ├── dengue.json
│   ├── diabetes.json
│   └── hyperthyroidism.json
├── frontend/
│   └── src/
│       ├── App.js           # React chat UI
│       └── App.css          # Premium dark theme
├── llm/
│   ├── config.py            # Model configuration
│   ├── prompts.py           # System & RAG prompts
│   ├── model_loader.py      # Ollama connection
│   └── response_generator.py # LLM response handler
├── rag/
│   ├── rag_pipeline.py      # RAG orchestrator
│   ├── context_builder.py   # Context formatting
│   ├── prompt_builder.py    # Prompt construction
│   └── response_parser.py   # Response cleanup
├── vector_db/
│   ├── vector_store.py      # Build FAISS index
│   ├── faiss_index.py       # FAISS operations
│   └── retriever.py         # Vector search
├── memory/
│   └── session_manager.py   # Session & history management
├── tools/
│   ├── emergency_tool.py    # Emergency detection
│   ├── doctor_search_tool.py # Doctor search
│   └── appointment_tool.py  # Appointment booking
├── requirements.txt
├── .env                     # Config (create manually)
└── README.md
```

---

## 📎 File Upload Support

Upload patient records for AI analysis:

| Format | Support |
|--------|---------|
| PDF | ✅ Text extraction (PyPDF2) |
| PNG/JPG | ✅ OCR with Tesseract (optional) |
| CSV | ✅ Table parsing |
| Excel (XLS/XLSX) | ✅ Multi-sheet support |
| TXT/JSON | ✅ Direct reading |

---

## ⚡ Speed Tips

| Method | Speed Boost |
|--------|------------|
| Use `llama3.2:1b` in `.env` | ~3x faster |
| NVIDIA GPU | ~10-20x faster |
| Use [Groq API](https://groq.com) | ~50x faster (free cloud) |

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## ⚠️ Disclaimer

MediBot provides **general health information only**. It is NOT a substitute for professional medical advice. Always consult a qualified healthcare provider for diagnosis and treatment.

---

## 📄 License

MIT License — free to use and modify.
