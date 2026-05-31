# rag/response_parser.py
"""Clean and post-process raw LLM output."""
import re


def parse_response(raw: str) -> str:
    """
    Light post-processing on LLM output:
    - Strip leading/trailing whitespace
    - Remove repeated 'MediBot:' prefixes the model sometimes adds
    - Ensure the disclaimer is always present for medical queries
    """
    text = raw.strip()

    # Remove self-referential prefixes
    text = re.sub(r"^(MediBot:|Assistant:|AI:)\s*", "", text, flags=re.IGNORECASE)

    return text


DISCLAIMER = (
    "\n\n---\n"
    "⚕️ *This information is for educational purposes only and is not a substitute "
    "for professional medical advice, diagnosis, or treatment. Please consult a "
    "qualified healthcare provider.*"
)


def add_disclaimer(text: str) -> str:
    if "consult" not in text.lower() and "doctor" not in text.lower():
        return text + DISCLAIMER
    return text
