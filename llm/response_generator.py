# llm/response_generator.py
"""
Calls the Ollama /api/chat endpoint and streams or returns the full response.
"""
import json
import requests
from typing import Generator

from llm.config import (
    OLLAMA_BASE_URL, OLLAMA_LLM_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS
)
from llm.prompts import SYSTEM_PROMPT


def generate_response(
    user_message: str,
    conversation_history: list[dict],
    system_prompt: str = SYSTEM_PROMPT,
    stream: bool = False,
) -> str | Generator:
    """
    Send a chat request to Ollama and return the assistant reply.

    Args:
        user_message:         The latest user message.
        conversation_history: List of {"role": ..., "content": ...} dicts.
        system_prompt:        Override the default system prompt if needed.
        stream:               If True, returns a generator that yields chunks.

    Returns:
        Full response string (stream=False) or a generator (stream=True).
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

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
        return _stream_response(url, payload)
    else:
        return _full_response(url, payload)


def _full_response(url: str, payload: dict) -> str:
    try:
        r = requests.post(url, json=payload, timeout=300)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        return "⚠️ Cannot connect to Ollama. Please ensure Ollama is running (`ollama serve`)."
    except requests.exceptions.Timeout:
        return "⚠️ The request timed out. The model may be loading — please try again."
    except Exception as e:
        return f"⚠️ Unexpected error: {str(e)}"


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
        yield f"⚠️ Streaming error: {str(e)}"


def generate_with_rag(
    user_message: str,
    context: str,
    conversation_history: list[dict],
) -> str:
    """Generate a response augmented with RAG context."""
    from llm.prompts import RAG_PROMPT_TEMPLATE

    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in conversation_history[-6:]  # last 3 turns
    )

    augmented_prompt = RAG_PROMPT_TEMPLATE.format(
        context=context,
        history=history_text,
        question=user_message,
    )

    # Use a single user message with the full augmented prompt
    payload = {
        "model":  OLLAMA_LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": augmented_prompt},
        ],
        "stream":  False,
        "options": {
            "temperature": LLM_TEMPERATURE,
            "num_predict": LLM_MAX_TOKENS,
        },
    }

    return _full_response(f"{OLLAMA_BASE_URL}/api/chat", payload)
