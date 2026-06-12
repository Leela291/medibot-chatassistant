# rag/rag_pipeline.py
"""
Main RAG pipeline: retrieve → build context → generate response.
"""
from vector_db.retriever import retrieve
from rag.context_builder import build_context
from rag.prompt_builder import build_rag_prompt
from rag.response_parser import parse_response
from llm.response_generator import generate_with_rag
from llm.config import TOP_K_RESULTS

# ─────────────────────────────────────────────────────────────
# Words to strip when building a Wikipedia search query.
# Keep medical/symptom words — only remove grammatical filler.
# ─────────────────────────────────────────────────────────────
QUERY_FILLER_WORDS = [
    "what", "is", "a", "an", "the", "define", "explain",
    "about", "how", "to", "for", "tell", "me", "please",
    "why", "am", "i", "are", "do", "does", "did", "was",
    "experiencing", "getting", "having", "feeling", "since",
    "yesterday", "today", "suddenly", "lately", "recently",
    "can", "could", "would", "should", "my", "your",
    "we", "they", "it", "this", "that", "these", "those",
]

import re

ALIASES = {
    "influenza": ["flu"],
    "flu": ["influenza"],
    "hypertension": ["high blood pressure"],
    "gastroenteritis": ["food poisoning", "stomach flu"],
}

def disease_matches_query(disease: str, query: str) -> bool:
    if not disease:
        return False

    disease = re.sub(r'[^a-zA-Z0-9 ]', ' ', disease.lower())
    query = query.lower()

    disease_terms = set(disease.split())

    for term in list(disease_terms):
        if term in ALIASES:
            disease_terms.update(ALIASES[term])

    return any(term in query for term in disease_terms)

def build_wikipedia_query(user_query: str) -> str:
    """
    Extract the core medical topic from a user query.
    
    Examples:
      "why am i experiencing throat pain since yesterday"
        → "throat pain causes"
      "what are the symptoms of food poisoning"
        → "food poisoning symptoms"
      "symptoms of constipation"
        → "constipation symptoms"
    """
    query = user_query.lower().strip("? .!")
    words = query.split()

    # Remove filler words
    keywords = [w for w in words if w not in QUERY_FILLER_WORDS and len(w) > 2]

    # Limit to 4 keywords max for clean Wikipedia search
    clean_query = " ".join(keywords[:4])

    return clean_query if clean_query else user_query


def validate_wikipedia_result(wiki_result: str, user_query: str) -> bool:
    """
    Check that the Wikipedia result actually matches the user's topic.
    Prevents using a 'food poisoning' article when user asked about 'throat pain'.
    """
    if not wiki_result:
        return False

    # Extract key topic words from query (ignore filler)
    query_words = [
        w for w in user_query.lower().split()
        if w not in QUERY_FILLER_WORDS and len(w) > 3
    ]

    # At least one key topic word must appear in the Wikipedia result
    result_lower = wiki_result.lower()
    matches = [w for w in query_words if w in result_lower]

    if not matches:
        print(f"[RAG Wikipedia] ❌ Discarded: result didn't match query keywords {query_words}")
        return False

    print(f"[RAG Wikipedia] ✅ Validated: matched keywords {matches}")
    return True

def run_rag(
    user_query: str,
    conversation_history: list[dict],
    top_k: int = TOP_K_RESULTS,
    stream: bool = False,
) -> dict:
    """
    Full RAG pipeline.
    """
    # 1. Retrieve relevant chunks
    retrieved_chunks = retrieve(user_query, top_k=top_k)

    # 2. Smart Validation (The Hard Mismatch Filter)
    needs_wikipedia = False
    
    if not retrieved_chunks:
        needs_wikipedia = True
    else:
        closest_chunk = retrieved_chunks[0]
        best_score = closest_chunk.get("score", 0.0)
        
        # Extract the disease name tag from the chunk
        chunk_disease = closest_chunk.get("disease", "")
        if isinstance(chunk_disease, dict):
            chunk_disease = chunk_disease.get("name", "")
        
        chunk_disease_clean = chunk_disease.lower().strip()
        query_clean = user_query.lower()

        # Reject Reason A: The math score is weak
        if best_score < 0.45:  # Threshold for relevance (tune as needed)
            needs_wikipedia = True
            retrieved_chunks = []
            
        # Reject Reason B: The chunk is about a specific disease NOT mentioned in the query
        elif chunk_disease_clean and chunk_disease_clean != "general":
            # If the database pulled a Diabetes chunk, but the user didn't ask about Diabetes...
            if not disease_matches_query(chunk_disease, user_query):
                print(f"[RAG Filter] Rejected {chunk_disease} context for query about '{user_query}'.")
                needs_wikipedia = True
                retrieved_chunks = []

    # 3. Wikipedia Fallback
    wikipedia_context = ""
    if needs_wikipedia:
        try:
            from tools.wikipedia_tool import get_wikipedia_disease_summary

            # Build a clean, specific search query
            clean_query = build_wikipedia_query(user_query)
            print(f"[RAG Wikipedia] Searching for: '{clean_query}' (from: '{user_query}')")

            wiki_summary = get_wikipedia_disease_summary(clean_query)

            # VALIDATE: Only use the result if it actually matches the topic
            if wiki_summary and validate_wikipedia_result(wiki_summary, user_query):
                wikipedia_context = wiki_summary
                print(f"[RAG Wikipedia] ✅ Used Wikipedia result for: {clean_query}")
            else:
                print(f"[RAG Wikipedia] ❌ Wikipedia result discarded — using general knowledge")

        except Exception as e:
            print(f"[RAG Wikipedia Fallback Error] {e}")

    # 4. Build readable context string
    if wikipedia_context:
        context = wikipedia_context + "\n\n" + build_context(retrieved_chunks)
    else:
        context = build_context(retrieved_chunks)

    for i, c in enumerate(retrieved_chunks):
        print(
            f"Chunk {i+1}: "
            f"score={c['score']} "
            f"disease={c['disease']}"
        )
        print("====== CHUNK ======")
        print(c["text"])
        print("===================\n")
    # 5. Generate LLM response with context
    raw_answer = generate_with_rag(
        user_message=user_query,
        context=context,
        conversation_history=conversation_history,
        stream=stream,
    )
    print("\n=== RAG CONTEXT ===")
    print(context)
    print("===================\n")

    # 6. Collect source diseases
    sources = []
    for c in retrieved_chunks:
        d = c.get("disease", "")
        if isinstance(d, dict):
            sources.append(d.get("name", "Local Database"))
        elif d:
            sources.append(d)
            
    sources = list(set(sources))
    
    if wikipedia_context:
        sources.append("Wikipedia Medical Encyclopedia")
    if not sources: 
        sources.append("General Medical Knowledge")

    if stream:
        return {
            "answer":  raw_answer,
            "sources": sources,
            "chunks":  retrieved_chunks,
        }
    
    # 7. Parse / clean the response
    parsed = parse_response(raw_answer)

    return {
        "answer":  parsed,
        "sources": sources,
        "chunks":  retrieved_chunks,
    }