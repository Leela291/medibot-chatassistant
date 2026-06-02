"""
Main RAG pipeline:
retrieve → validate → build context → generate response
Supports local medical DB + Wikipedia fallback
"""

from vector_db.retriever import retrieve
from rag.context_builder import build_context
from rag.response_parser import parse_response
from llm.response_generator import generate_with_rag
from llm.config import TOP_K_RESULTS


# ─────────────────────────────────────────────
# SYMPTOM DETECTION (from Lee branch, improved)
# ─────────────────────────────────────────────
SYMPTOM_WORDS = [
    "pain", "ache", "fever", "cough", "cold",
    "headache", "nausea", "vomiting",
    "dizziness", "fatigue", "weakness",
    "body pain", "stomach pain", "chest pain",
    "sore throat", "runny nose",
    "diarrhea", "constipation"
]


def is_symptom_query(query: str) -> bool:
    query = query.lower()
    return any(word in query for word in SYMPTOM_WORDS)


# ─────────────────────────────────────────────
# MAIN RAG PIPELINE
# ─────────────────────────────────────────────
def run_rag(
    user_query: str,
    conversation_history: list[dict],
    top_k: int = TOP_K_RESULTS,
    stream: bool = False,
) -> dict:
    """
    Full RAG pipeline:
    retrieve → validate → context build → LLM generation
    """

    # --------------------------------------------------
    # 1. Retrieve local medical knowledge
    # --------------------------------------------------
    retrieved_chunks = retrieve(user_query, top_k=top_k)

    # --------------------------------------------------
    # 2. Smart filtering (Main branch logic improved)
    # --------------------------------------------------
    needs_wikipedia = False

    if not retrieved_chunks:
        needs_wikipedia = True
    else:
        best = retrieved_chunks[0]
        score = best.get("score", 0.0)

        disease = best.get("disease", "")
        if isinstance(disease, dict):
            disease = disease.get("name", "")

        disease = str(disease).lower().strip()
        query = user_query.lower()

        # Weak match → fallback
        if score > 0.85:
            needs_wikipedia = True
            retrieved_chunks = []

        # Disease mismatch → fallback
        elif disease and disease != "general":
            if disease not in query:
                needs_wikipedia = True
                retrieved_chunks = []

    # --------------------------------------------------
    # 3. Wikipedia fallback
    # --------------------------------------------------
    wikipedia_context = ""

    if needs_wikipedia:
        try:
            from tools.wikipedia_tool import get_wikipedia_disease_summary

            clean_query = user_query.lower()

            remove_words = [
                "what", "is", "a", "an", "the", "define",
                "explain", "symptoms", "of", "treatment",
                "for", "cause", "causes", "about", "how",
                "to", "cure", "diagnose"
            ]

            for w in remove_words:
                clean_query = clean_query.replace(w, "")

            clean_query = clean_query.strip(" ?.!")

            wiki_summary = get_wikipedia_disease_summary(clean_query)

            if wiki_summary:
                wikipedia_context = wiki_summary

        except Exception as e:
            print(f"[Wikipedia Error] {e}")

    # --------------------------------------------------
    # 4. Build final context (smart merging)
    # --------------------------------------------------
    local_context = build_context(retrieved_chunks)

    if wikipedia_context:
        if is_symptom_query(user_query):
            context = f"""
GENERAL MEDICAL INFORMATION:
{wikipedia_context}

LOCAL MEDICAL DATA:
{local_context}
"""
        else:
            context = f"""
LOCAL MEDICAL DATA:
{local_context}

GENERAL MEDICAL INFORMATION:
{wikipedia_context}
"""
    else:
        context = local_context

    # --------------------------------------------------
    # 5. Generate response
    # --------------------------------------------------
    raw_answer = generate_with_rag(
        user_message=user_query,
        context=context,
        conversation_history=conversation_history,
        stream=stream,
    )

    # --------------------------------------------------
    # 6. Parse response
    # --------------------------------------------------
    parsed = parse_response(raw_answer)

    # --------------------------------------------------
    # 7. Build sources
    # --------------------------------------------------
    sources = []

    for c in retrieved_chunks:
        d = c.get("disease", "")

        if isinstance(d, dict):
            d = d.get("name", "")

        if d and d not in sources:
            sources.append(d)

    if wikipedia_context:
        sources.append("Wikipedia Medical Encyclopedia")

    if not sources:
        sources.append("General Medical Knowledge")

    # --------------------------------------------------
    # 8. Return final output
    # --------------------------------------------------
    return {
        "answer": parsed,
        "sources": sources,
        "chunks": retrieved_chunks,
    }
