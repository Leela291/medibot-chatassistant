"""
Unified response generator:
- Primary: Ollama
- Fallback: Gemini (if enabled)
- Supports streaming + RAG
"""

import os
import json
import requests
from typing import Generator

from llm.config import (
    OLLAMA_BASE_URL, OLLAMA_LLM_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS, GEMINI_MODEL
)
from llm.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE


# ─────────────────────────────────────────────
# GEMINI KEY
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY = GEMINI_API_KEY if GEMINI_API_KEY and GEMINI_API_KEY.strip() else None


# ─────────────────────────────────────────────
# OLLAMA FULL RESPONSE
# ─────────────────────────────────────────────
def _full_response(url: str, payload: dict) -> str:
    try:
        r = requests.post(url, json=payload, timeout=300)
        r.raise_for_status()
        return r.json()["message"]["content"]

    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────
# OLLAMA STREAM RESPONSE
# ─────────────────────────────────────────────
def _stream_response(url: str, payload: dict) -> Generator:
    try:
        with requests.post(url, json=payload, stream=True, timeout=300) as r:
            r.raise_for_status()

            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break

    except Exception as e:
        yield f"⚠️ Streaming error: {e}"


# ─────────────────────────────────────────────
# GEMINI FALLBACK
# ─────────────────────────────────────────────
def _fallback_to_gemini(messages, system_prompt, stream: bool):
    if not GEMINI_API_KEY:
        msg = "⚠️ MediBot offline (Ollama failed & no Gemini key)."
        return (lambda: (yield msg))() if stream else msg

    try:
        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            contents.append({
                "role": "model" if m["role"] == "assistant" else "user",
                "parts": [{"text": m["content"]}]
            })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "temperature": LLM_TEMPERATURE,
                "maxOutputTokens": LLM_MAX_TOKENS,
            }
        }

        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()

        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]

        if stream:
            def gen():
                for w in text.split():
                    yield w + " "
            return gen()

        return text

    except Exception as e:
        msg = f"⚠️ Both Ollama & Gemini failed: {e}"
        return (lambda: (yield msg))() if stream else msg


# ─────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────
def generate_response(
    user_message: str,
    conversation_history: list[dict],
    system_prompt: str = SYSTEM_PROMPT,
    stream: bool = False,
) -> str | Generator:

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": OLLAMA_LLM_MODEL,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": LLM_TEMPERATURE,
            "num_predict": LLM_MAX_TOKENS,
        },
    }

    url = f"{OLLAMA_BASE_URL}/api/chat"

    # ── Try Ollama first ──
    if stream:
        try:
            r = requests.post(url, json=payload, stream=True, timeout=180)
            r.raise_for_status()
            return _stream_response(url, payload)
        except Exception:
            return _fallback_to_gemini(messages, system_prompt, stream)

    else:
        result = _full_response(url, payload)

        if result is not None:
            return result

        return _fallback_to_gemini(messages, system_prompt, stream)


# ─────────────────────────────────────────────
# RAG GENERATOR
# ─────────────────────────────────────────────
def generate_with_rag(
    user_message: str,
    context: str,
    conversation_history: list[dict],
    stream: bool = False,
) -> str | Generator:

    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in conversation_history[-6:]
    )

    augmented_prompt = RAG_PROMPT_TEMPLATE.format(
        context=context,
        history=history_text,
        question=user_message,
    )

    return generate_response(
        user_message=augmented_prompt,
        conversation_history=[],
        system_prompt=SYSTEM_PROMPT,
        stream=stream,
    )
