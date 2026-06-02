# services/symptom_detector.py
"""
Detect when the user is reporting symptoms (vs asking general medical facts)
and whether structured follow-up questions should be shown first.
"""

import re

# Longest phrases first so "chest pain" wins over partial matches
SYMPTOM_PHRASES = [
    ("shortness of breath", "shortness of breath"),
    ("body pain", "body pain"),
    ("stomach pain", "stomach pain"),
    ("chest pain", "chest pain"),
    ("sore throat", "sore throat"),
    ("runny nose", "runny nose"),
    ("muscle ache", "body pain"),
    ("body ache", "body pain"),
    ("headache", "headache"),
    ("migraine", "headache"),
    ("vomiting", "stomach pain"),
    ("nausea", "stomach pain"),
    ("diarrhea", "stomach pain"),
    ("constipation", "stomach pain"),
    ("dizziness", "headache"),
    ("fatigue", "body pain"),
    ("weakness", "body pain"),
    ("rash", "general"),
    ("chills", "fever"),
    ("fever", "fever"),
    ("cough", "cough"),
    ("cold", "cough"),
]

# User is asking for facts, not describing their own illness
INFORMATIONAL_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bwhat (is|are)\b",
        r"\btell me about\b",
        r"\bhow (to|do i|can i) (treat|prevent|manage|cure)\b",
        r"\b(symptoms|treatment|prevention|causes|food) of\b",
        r"\babout (the )?(disease|condition|illness)\b",
        r"\bdefine\b",
        r"\bexplain\b",
        r"\bdifference between\b",
    ]
]

# Vague health complaints — Claude-style "ask before answering"
VAGUE_SYMPTOM_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(i |i'm |im )(feel|feeling) (sick|unwell|bad|terrible|awful|wrong|off)\b",
        r"\bnot feeling (well|good|right)\b",
        r"\bsomething (is|feels) wrong\b",
        r"\b(i |i'm )sick\b",
        r"\bhealth (problem|issue)\b",
        r"\bi need (help|advice)\b",
        r"\bcan you help\b",
        r"\bdon'?t know what'?s wrong\b",
        r"\bwhat'?s wrong with me\b",
        r"\bi have (a )?(problem|issue)\b",
        r"\bmedical (help|advice)\b",
        r"\bcheck my symptoms\b",
        r"\bi (have|got) symptoms\b",
        r"\bnot sure what i have\b",
    ]
]

# Very short messages that look like symptom reports, not disease Q&A
VAGUE_SHORT_MAX_WORDS = 8
VAGUE_SHORT_HINTS = (
    "hurt", "pain", "sick", "unwell", "wrong", "symptom", "problem", "help",
)


def is_informational_query(text: str) -> bool:
    """True when the user wants disease facts, not personal triage."""
    return any(p.search(text) for p in INFORMATIONAL_PATTERNS)


def detect_symptom(text: str) -> str | None:
    """Return triage key if a known symptom phrase appears in the message."""
    lowered = text.lower()
    for phrase, triage_key in SYMPTOM_PHRASES:
        if phrase in lowered:
            return triage_key
    return None


def is_vague_symptom_report(text: str) -> bool:
    """True when the user seems unwell but did not give enough clinical detail."""
    if is_informational_query(text):
        return False

    if any(p.search(text) for p in VAGUE_SYMPTOM_PATTERNS):
        return True

    words = text.split()
    if len(words) <= VAGUE_SHORT_MAX_WORDS:
        lowered = text.lower()
        if any(h in lowered for h in VAGUE_SHORT_HINTS) and not is_informational_query(text):
            # e.g. "I feel sick" / "help me"
            if re.search(r"\b(i |i'm |my |me |help|sick|unwell|pain|hurt)\b", lowered):
                return True

    return False


def should_start_triage(text: str, skip_detection: bool = False) -> tuple[bool, str | None]:
    """
    Decide if we should show follow-up questions before running RAG.

    Returns:
        (should_triage, triage_key)
        triage_key is a key in TRIAGE_QUESTIONS, or "general" for vague reports.
    """
    if skip_detection or not text.strip():
        return False, None

    if is_informational_query(text):
        return False, None

    symptom = detect_symptom(text)
    if symptom:
        return True, symptom

    if is_vague_symptom_report(text):
        return True, "general"

    return False, None
