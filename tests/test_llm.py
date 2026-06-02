"""
Tests for the LLM response generation module.
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import pytest
from llm.response_generator import (
    generate_response,
    generate_with_rag
)
from llm.model_loader import check_ollama_connection


# ─────────────────────────────────────────────
# OLLAMA CONNECTION TEST
# ─────────────────────────────────────────────
class TestOllamaConnection:

    def test_connection_check_returns_bool(self):
        result = check_ollama_connection()
        assert isinstance(result, bool)


# ─────────────────────────────────────────────
# RESPONSE GENERATOR TESTS
# ─────────────────────────────────────────────
class TestResponseGenerator:

    @patch("llm.response_generator.requests.post")
    def test_generate_response_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "message": {
                    "content": "Diabetes is a chronic condition."
                }
            },
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = generate_response("What is diabetes?", [])

        assert isinstance(result, str)
        assert "diabetes" in result.lower()


    @patch("llm.response_generator.requests.post")
    def test_generate_response_connection_error(self, mock_post):
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError()

        result = generate_response("What is diabetes?", [])

        # safer assertion
        assert isinstance(result, str)
        assert len(result) > 0


    @patch("llm.response_generator.requests.post")
    def test_generate_with_rag(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "message": {
                    "content": "Diabetes symptoms include frequent urination."
                }
            },
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = generate_with_rag(
            user_message="What are the symptoms?",
            context="Diabetes: frequent urination, excessive thirst.",
            conversation_history=[],
        )

        assert isinstance(result, str)
        assert len(result) > 0


# ─────────────────────────────────────────────
# PROMPT VALIDATION TESTS
# ─────────────────────────────────────────────
class TestPrompts:

    def test_system_prompt_exists(self):
        from llm.prompts import SYSTEM_PROMPT

        assert len(SYSTEM_PROMPT) > 100
        assert "medical" in SYSTEM_PROMPT.lower()


    def test_rag_template_has_placeholders(self):
        from llm.prompts import RAG_PROMPT_TEMPLATE

        assert "{context}" in RAG_PROMPT_TEMPLATE
        assert "{question}" in RAG_PROMPT_TEMPLATE
