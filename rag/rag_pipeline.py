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
) -> dict:
    """
    Full RAG pipeline.

    Returns:
        {
            "answer":   str,          # final response text
            "sources":  list[str],    # disease sources used
            "chunks":   list[dict],   # raw retrieved chunks
        }
    """
    # 1. Retrieve relevant chunks
    retrieved_chunks = retrieve(user_query, top_k=top_k)

    # 2. Build readable context string
    context = build_context(retrieved_chunks)

    # 3. Generate LLM response with context
    raw_answer = generate_with_rag(
        user_message=user_query,
        context=context,
        conversation_history=conversation_history,
    )

    # 4. Parse / clean the response
    parsed = parse_response(raw_answer)

    # 5. Collect source diseases
    sources = list({c["disease"] for c in retrieved_chunks})

    return {
        "answer":  parsed,
        "sources": sources,
        "chunks":  retrieved_chunks,
    }
