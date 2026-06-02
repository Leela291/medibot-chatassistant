# rag/context_builder.py
"""Formats retrieved chunks into a clean context string for the LLM."""


def build_context(chunks: list[dict], max_chars: int = 1200) -> str:
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
    separator = "\n\n"

    for chunk in chunks:
        disease = chunk.get("disease", "Unknown")
        text = chunk.get("text", "").strip()
        entry = f"{disease}\n{text}"

        projected = separator.join(sections + [entry]) if sections else entry
        if len(projected) <= max_chars:
            sections.append(entry)
            continue

        if not sections:
            prefix = f"{disease}\n"
            budget = max_chars - len(prefix)
            if budget > 0:
                sections.append(prefix + text[:budget].rstrip())
        break

    return separator.join(sections)
