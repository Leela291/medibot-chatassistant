# llm/response_generator.py
import json
import requests
import os
from typing import Generator

from llm.config import (
    OLLAMA_BASE_URL, OLLAMA_LLM_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS, GEMINI_MODEL
)
from llm.prompts import SYSTEM_PROMPT

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "":
    GEMINI_API_KEY = None

def generate_response(
    user_message: str,
    conversation_history: list[dict],
    system_prompt: str = SYSTEM_PROMPT,
    stream: bool = False,
    images: list[str] = None,
) -> str | Generator:
    """
    Send a chat request to Ollama FIRST. If it fails, fallback to Gemini.
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    # ── Fallback Logic (Gemini) ──
    def fallback_to_gemini():
        if not GEMINI_API_KEY:
            err_msg = "⚠️ **MediBot is offline (Local Ollama failed & No Gemini Key found).**\nPlease ensure Ollama is running (`ollama serve`) or add a GEMINI_API_KEY to your .env file."
            if stream:
                def _err_gen(): yield err_msg
                return _err_gen()
            return err_msg
        
        try:
            print("[Router] Ollama connection failed. Falling back to Gemini API...")
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
            r = requests.post(url, json=payload, timeout=20)
            r.raise_for_status()
            content = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            
            if stream:
                def _cloud_generator(text):
                    words = text.split(" ")
                    for idx, w in enumerate(words):
                        space = " " if idx < len(words) - 1 else ""
                        yield w + space
                return _cloud_generator(content)
            return content
            
        except Exception as e:
            err_msg = f"⚠️ **Both Local Ollama and Cloud Gemini APIs are currently unreachable.** ({e})"
            if stream:
                def _fail_gen(): yield err_msg
                return _fail_gen()
            return err_msg

    # ── Primary Logic (Ollama) ──
    payload = {
        "model":   OLLAMA_LLM_MODEL,
        "messages": messages,
        "stream":  stream,
        "options": {
            "temperature": LLM_TEMPERATURE,
            "num_predict": LLM_MAX_TOKENS,
        },
    }

    url = f"{OLLAMA_BASE_URL}/api/chat"

    if stream:
        try:
            r = requests.post(url, json=payload, stream=True, timeout=180)
            r.raise_for_status()
            def _stream_gen():
                for line in r.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
            return _stream_gen()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return fallback_to_gemini()
        except Exception:
            return fallback_to_gemini()
    else:
        try:
            r = requests.post(url, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()["message"]["content"]
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return fallback_to_gemini()
        except Exception:
            return fallback_to_gemini()


def generate_with_rag(
    user_message: str,
    context: str,
    conversation_history: list[dict],
    images: list[str] = None,
    stream: bool = False,
) -> str | Generator:
    """Generate a response augmented with RAG context."""
    from llm.prompts import RAG_PROMPT_TEMPLATE

    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in conversation_history[-3:]  # last 3 turns
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
        images=images,
        stream=stream,
    )