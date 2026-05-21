# rag/prompt_builder.py
"""Builds the final augmented prompt for RAG inference."""

from llm.prompts import RAG_PROMPT_TEMPLATE


def build_rag_prompt(
    question: str,
    context: str,
    history: list[dict],
) -> str:
    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in history[-2:]
    )
    return RAG_PROMPT_TEMPLATE.format(
        context=context,
        history=history_text or "No previous conversation.",
        question=question,
    )
