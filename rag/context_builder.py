"""
Formats retrieved chunks into a clean context string for the LLM.
"""

from typing import List, Dict


# ─────────────────────────────────────────────
# CONTEXT BUILDER
# ─────────────────────────────────────────────
def build_context(chunks: List[Dict], max_chars: int = 1200) -> str:
    """
    Build a formatted context block from retrieved chunks.

    Args:
        chunks: List of chunk dicts with 'text', 'disease', 'score'
        max_chars: Soft character limit for LLM context

    Returns:
        Formatted context string
    """

    if not chunks:
        return "No specific medical knowledge retrieved for this query."

    sections = []
    separator = "\n\n"
    total_chars = 0

    for chunk in chunks:
        disease = chunk.get("disease", "Unknown")
        text = chunk.get("text", "").strip()

        if not text:
            continue

        entry = f"{disease}\n{text}"

        # ── Case 1: fits fully ──
        if total_chars + len(entry) <= max_chars:
            sections.append(entry)
            total_chars += len(entry)

        # ── Case 2: partial fit ──
        else:
            remaining = max_chars - total_chars

            if remaining > 50:  # only include if meaningful space left
                truncated_text = text[:remaining - len(disease) - 1].rstrip()
                sections.append(f"{disease}\n{truncated_text}")

            break  # stop once limit is reached

    return separator.join(sections)
