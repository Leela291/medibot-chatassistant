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

        # Reject Reason A: The math score is weak (distance > 0.85)
        if best_score > 0.85:
            needs_wikipedia = True
            retrieved_chunks = []
            
        # Reject Reason B: The chunk is about a specific disease NOT mentioned in the query
        elif chunk_disease_clean and chunk_disease_clean != "general":
            # If the database pulled a Diabetes chunk, but the user didn't ask about Diabetes...
            if chunk_disease_clean not in query_clean:
                print(f"[RAG Filter] Rejected {chunk_disease} context for query about '{user_query}'.")
                needs_wikipedia = True
                retrieved_chunks = [] # Trash the irrelevant context!

    # 3. Wikipedia Fallback
    wikipedia_context = ""
    if needs_wikipedia:
        try:
            from tools.wikipedia_tool import get_wikipedia_disease_summary
            # Strip conversational words to improve Wiki search
            clean_query = user_query.lower()
            for word in ["what", "is", "a", "an", "the", "define", "explain", "symptoms", "of", "treatment", "for", "cause", "causes", "about", "how", "to", "cure", "diagnose", "food", "recommended"]:
                clean_query = clean_query.replace(f" {word} ", " ").replace(f"{word} ", "").replace(f" {word}", "")
            clean_query = clean_query.strip("? .!").strip()
            
            wiki_summary = get_wikipedia_disease_summary(clean_query)
            if wiki_summary:
                wikipedia_context = wiki_summary
                print(f"[RAG Wikipedia Fallback] Fetched Wikipedia info for: {clean_query}")
        except Exception as e:
            print(f"[RAG Wikipedia Fallback Error] {e}")

    # 4. Build readable context string
    if wikipedia_context:
        context = wikipedia_context + "\n\n" + build_context(retrieved_chunks)
    else:
        context = build_context(retrieved_chunks)

    # 5. Generate LLM response with context
    raw_answer = generate_with_rag(
        user_message=user_query,
        context=context,
        conversation_history=conversation_history,
        stream=stream,
    )

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