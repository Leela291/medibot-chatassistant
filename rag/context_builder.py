# rag/context_builder.py
"""Formats retrieved chunks into a clean context string for the LLM."""


def build_context(chunks: list[dict], max_chars: int = 3000) -> str:
    """
    Build a formatted context block from retrieved chunks.

    Args:
        chunks:    List of chunk dicts with 'text', 'disease', 'score'.
        max_chars: Soft limit on total context characters.

    Returns:
        A single formatted string to inject into the prompt.
    """
    if not chunks:
        return "No specific medical knowledge retrieved for this query."

    sections = []
    total = 0

    for i, chunk in enumerate(chunks, start=1):
        disease = chunk.get("disease", "Unknown")
        text    = chunk.get("text", "").strip()
        score   = chunk.get("score", 0.0)

        entry = f"[{i}] Disease: {disease} (relevance: {score:.2f})\n{text}"
        total += len(entry)

        if total > max_chars and sections:
            break   # stop adding if we've exceeded the soft limit

        sections.append(entry)

    return "\n\n".join(sections)
