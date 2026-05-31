# rag/prompt_builder.py
"""Builds the final augmented prompt for RAG inference."""

from llm.prompts import RAG_PROMPT_TEMPLATE


def build_rag_prompt(
    question: str,
    context: str,
    history: list[dict],
) -> str:
    
    # =========================================
    # Format recent conversation history
    # =========================================
    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in history[-2:]
    )

    # =========================================
    # Empty context fallback
    # =========================================
    if not context.strip():
        context = (
            "No reliable medical context found."
        )

    # =========================================
    # Safety instructions
    # =========================================
    extra_rules = """
    IMPORTANT RULES:

    - Only use medical context relevant to the user's question
    - Ignore unrelated diseases or symptoms
    - Never combine unrelated diseases
    - Do not invent medical facts
    - If context is weak or unrelated, rely on general medical knowledge
    - Keep answers concise and medically accurate
    - Avoid repeating unnecessary warnings
    """

    # =========================================
    # Final prompt assembly
    # =========================================
    final_prompt = RAG_PROMPT_TEMPLATE.format(
        context=context,
        history=(
            history_text
            or
            "No previous conversation."
        ),
        question=question,
    )

    # =========================================
    # Add extra safety rules
    # =========================================
    final_prompt += f"\n\n{extra_rules}"
    return final_prompt