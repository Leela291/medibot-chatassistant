"""
Main RAG pipeline: retrieve → build context → generate response.
Uses both local medical datasets and Wikipedia.
"""

from vector_db.retriever import retrieve
from rag.context_builder import build_context
from rag.response_parser import parse_response
from llm.response_generator import generate_with_rag
from llm.config import TOP_K_RESULTS


SYMPTOM_WORDS = [
    "pain", "ache", "fever", "cough", "cold",
    "headache", "nausea", "vomiting",
    "dizziness", "fatigue", "weakness",
    "body pain", "body pains",
    "stomach pain", "chest pain",
    "sore throat", "runny nose",
    "diarrhea", "constipation"
]


def is_symptom_query(query: str) -> bool:
    query = query.lower()

    return any(
        symptom in query
        for symptom in SYMPTOM_WORDS
    )


def run_rag(
    user_query: str,
    conversation_history: list[dict],
    top_k: int = TOP_K_RESULTS,
) -> dict:
    """
    Full RAG pipeline.

    Returns:
    {
        "answer": str,
        "sources": list[str],
        "chunks": list[dict]
    }
    """

    # --------------------------------------------------
    # 1. Retrieve local medical knowledge
    # --------------------------------------------------
    retrieved_chunks = retrieve(
        user_query,
        top_k=top_k
    )

    local_context = build_context(retrieved_chunks)

    # --------------------------------------------------
    # 2. Retrieve Wikipedia knowledge
    # --------------------------------------------------
    wiki_context = ""
    wikipedia_used = False

    try:
        from tools.wikipedia_tool import get_wikipedia_context

        wiki_context = get_wikipedia_context(user_query)

        if wiki_context:
            wikipedia_used = True

    except Exception as e:
        print(f"[Wikipedia Error] {e}")

    # --------------------------------------------------
    # 3. Combine contexts intelligently
    # --------------------------------------------------
    if is_symptom_query(user_query):

        context = f"""
GENERAL MEDICAL INFORMATION:
{wiki_context}

LOCAL MEDICAL DATA:
{local_context}
"""

    else:

        context = f"""
LOCAL MEDICAL DATA:
{local_context}

GENERAL MEDICAL INFORMATION:
{wiki_context}
"""

    # --------------------------------------------------
    # 4. Generate response
    # --------------------------------------------------
    raw_answer = generate_with_rag(
        user_message=user_query,
        context=context,
        conversation_history=conversation_history,
    )

    # --------------------------------------------------
    # 5. Clean response
    # --------------------------------------------------
    parsed_answer = parse_response(raw_answer)

    # --------------------------------------------------
    # 6. Collect sources
    # --------------------------------------------------
    sources = []

    for chunk in retrieved_chunks:

        disease = chunk.get("disease")

        if isinstance(disease, dict):
            disease_name = disease.get("name")
        else:
            disease_name = disease

        if disease_name and disease_name not in sources:
            sources.append(disease_name)

    if wikipedia_used:
        sources.append("Wikipedia")

    return {
        "answer": parsed_answer,
        "sources": sources,
        "chunks": retrieved_chunks,
    }