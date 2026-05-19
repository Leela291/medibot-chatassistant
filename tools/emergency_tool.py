# tools/emergency_tool.py
"""
Detects emergency keywords in user messages and returns an immediate
emergency response without waiting for the LLM.
"""
import re

EMERGENCY_KEYWORDS = [
    r"\bchest pain\b", r"\bheart attack\b", r"\bstroke\b",
    r"\bcan'?t breathe\b", r"\bcannot breathe\b", r"\bstopped breathing\b",
    r"\bseizure\b", r"\bunconscious\b", r"\bnot responding\b",
    r"\bsevere bleeding\b", r"\bheavy bleeding\b", r"\bblood loss\b",
    r"\bsuicide\b", r"\bkill myself\b", r"\bself harm\b",
    r"\bdrowning\b", r"\bpoisoning\b", r"\boverdose\b",
    r"\bhigh fever.*child\b", r"\bfebrile seizure\b",
    r"\bdiabetic coma\b", r"\bketoacidosis\b",
    r"\bthyroid storm\b", r"\bsevere allergic\b", r"\banaphylaxis\b",
]

_PATTERNS = [re.compile(kw, re.IGNORECASE) for kw in EMERGENCY_KEYWORDS]

EMERGENCY_RESPONSE = """🚨 **EMERGENCY — Please act immediately!**

**Call emergency services NOW:**
- 🇮🇳 **India**: Ambulance → **108** | General Emergency → **112**
- 🌍 International: Local emergency number

**While waiting for help:**
1. Keep the person calm and lying down (unless vomiting — turn on side)
2. Do NOT give food, water, or medication unless directed by a medical professional
3. If the person is unconscious and not breathing — start CPR if trained
4. Stay on the line with emergency services

**Do NOT delay** — please call emergency services immediately.

---
If this was not an emergency, please describe your symptoms in more detail and I'll help you further.
"""


def is_emergency(message: str) -> bool:
    """Return True if the message contains emergency indicators."""
    return any(p.search(message) for p in _PATTERNS)


def handle_emergency(message: str) -> dict | None:
    """
    If message is an emergency, return an immediate response dict.
    Otherwise return None.
    """
    if is_emergency(message):
        return {
            "answer":    EMERGENCY_RESPONSE,
            "sources":   [],
            "is_emergency": True,
        }
    return None
