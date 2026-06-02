"""
Clean and post-process raw LLM output.
"""

import re


# ─────────────────────────────────────────────
# MAIN RESPONSE CLEANER
# ─────────────────────────────────────────────
def parse_response(raw: str) -> str:
    """
    Light post-processing on LLM output:
    - Strip whitespace
    - Remove repeated role prefixes
    """

    text = raw.strip()

    # Remove unwanted prefixes
    text = re.sub(
        r"^(MediBot:|Assistant:|AI:)\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text


# ─────────────────────────────────────────────
# MEDICAL DISCLAIMER
# ─────────────────────────────────────────────
DISCLAIMER = (
    "\n\n---\n"
    "⚕️ *This information is for educational purposes only and is not a substitute "
    "for professional medical advice, diagnosis, or treatment. Please consult a "
    "qualified healthcare provider.*"
)


# ─────────────────────────────────────────────
# DISCLAIMER ATTACHER
# ─────────────────────────────────────────────
def add_disclaimer(text: str) -> str:
    """
    Adds disclaimer only when not already implied.
    """

    if "consult" not in text.lower() and "doctor" not in text.lower():
        return text + DISCLAIMER

    return text
