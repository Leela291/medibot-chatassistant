# tools/emergency_tool.py
"""
Fixed emergency tool — only triggers for EXPLICIT life-threatening statements.
General health questions (symptoms, causes, food poisoning, throat pain) 
are NEVER treated as emergencies.
"""

# ─────────────────────────────────────────────────────────────
# EXPLICIT emergency phrases — ALL of these must match exactly
# These are things only someone in active crisis would say
# ─────────────────────────────────────────────────────────────
EMERGENCY_PHRASES = [
    "cannot breathe", "can't breathe", "cant breathe",
    "not breathing", "stopped breathing",
    "unconscious", "unresponsive", "not responding",
    "collapsing", "i am collapsing", "i'm collapsing",
    "call ambulance", "need ambulance", "send ambulance",
    "i am dying", "i'm dying", "going to die",
    "heart attack", "having a stroke",
    "severe chest pain", "chest pain radiating",
    "swallowed poison", "drank poison", "took poison",
    "overdose", "took too many pills",
    "choking right now", "someone is choking",
    "bleeding heavily", "won't stop bleeding",
    "seizure right now", "having a seizure",
    "emergency help", "need emergency",
    "call 108", "call 112", "call 911",
]

# ─────────────────────────────────────────────────────────────
# SAFE words — if the message contains these, it is a general
# health question, NOT an emergency. Never trigger emergency
# when these are the main subject of the message.
# ─────────────────────────────────────────────────────────────
INFORMATIONAL_SAFE_WORDS = [
    "what are", "what is", "symptoms of", "causes of",
    "how does", "how do", "explain", "tell me about",
    "why do i", "why does", "how to treat", "how to prevent",
    "signs of", "difference between", "define", "meaning of",
    "food poisoning", "constipation", "diarrhea", "nausea",
    "throat pain", "headache", "fever", "vomiting",
    "stomach ache", "food safety", "what causes",
]

EMERGENCY_RESPONSE = """🚨 This sounds like a medical emergency. Please act immediately!

**Call emergency services NOW:**
- 🇮🇳 India: Ambulance → **108** | General Emergency → **112**
- 🌍 International: Your local emergency number

**While waiting for help:**
1. Keep the person calm and lying down (turn on side if vomiting)
2. Do NOT give food, water, or medication unless directed by medical staff
3. If unconscious and not breathing — start CPR if trained
4. Stay on the line with emergency services

---
*If this was not an emergency, please rephrase your question and I'll help you.*"""


def classify_intent(message: str) -> str:
    """
    Classify message intent before any response is generated.
    
    Returns:
        'EMERGENCY'      — explicit life-threatening crisis
        'INFORMATIONAL'  — general health question  
        'PERSONAL'       — user feels unwell but not in crisis
    """
    msg = message.lower().strip()

    # Step 1: Check for informational safe words FIRST
    # If the message is clearly a question, it's never an emergency
    is_informational = any(phrase in msg for phrase in INFORMATIONAL_SAFE_WORDS)
    if is_informational:
        return "INFORMATIONAL"

    # Step 2: Check for explicit emergency phrases
    is_emergency = any(phrase in msg for phrase in EMERGENCY_PHRASES)
    if is_emergency:
        return "EMERGENCY"

    # Step 3: Personal concern (user feels unwell but not in crisis)
    personal_indicators = [
        "i feel", "i have", "i am feeling", "i've been",
        "i think i", "i ate", "my stomach", "my throat",
        "i got", "i'm feeling", "i'm having", "i feel sick"
    ]
    is_personal = any(phrase in msg for phrase in personal_indicators)
    if is_personal:
        return "PERSONAL"

    # Default: informational (safer than triggering false emergency)
    return "INFORMATIONAL"


def handle_emergency(message: str) -> dict | None:
    """
    Returns emergency response dict ONLY for genuine emergencies.
    Returns None for all general health questions.

    This replaces the old handle_emergency() that was triggering
    on any mention of health symptoms.
    """
    intent = classify_intent(message)

    if intent == "EMERGENCY":
        print(f"[Emergency Tool] ⚠️  EMERGENCY detected: '{message[:60]}'")
        return {
            "answer": EMERGENCY_RESPONSE,
            "is_emergency": True,
            "intent": "EMERGENCY"
        }

    # All non-emergency messages return None
    # chatbot_api.py will then proceed with normal RAG/LLM response
    print(f"[Emergency Tool] ✅ Intent={intent}, no emergency triggered for: '{message[:60]}'")
    return None
