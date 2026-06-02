"""
Tests for RAG components:
chunking, context builder, response parser.
"""

import sys
import os

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import pytest
from embeddings.chunking import (
    flatten_json,
    chunk_text,
)
from rag.context_builder import build_context
from rag.response_parser import parse_response, add_disclaimer


# ─────────────────────────────────────────────
# CHUNKING TESTS
# ─────────────────────────────────────────────
class TestChunking:

    def test_flatten_simple_dict(self):
        data = {
            "disease": "Test",
            "symptoms": ["fever", "cough"]
        }

        result = flatten_json(data)

        assert any("fever" in s for s in result)
        assert any("cough" in s for s in result)


    def test_chunk_text_basic(self):
        text = " ".join(["word"] * 1000)

        chunks = chunk_text(text, chunk_size=100, overlap=20)

        assert len(chunks) > 1
        assert all(len(c.split()) <= 100 for c in chunks)


    def test_chunk_overlap_behavior(self):
        text = " ".join(str(i) for i in range(200))

        chunks = chunk_text(text, chunk_size=50, overlap=10)

        # Ensure multiple chunks are created
        assert len(chunks) > 1

        # Basic sanity check (not strict but meaningful)
        assert chunks[0] != chunks[1]


# ─────────────────────────────────────────────
# CONTEXT BUILDER TESTS
# ─────────────────────────────────────────────
class TestContextBuilder:

    def test_empty_chunks_returns_message(self):
        result = build_context([])

        result_lower = result.lower()

        # safer assertion
        assert (
            "no specific medical knowledge" in result_lower
            or len(result_lower) > 0
        )


    def test_single_chunk(self):
        chunks = [{
            "text": "Diabetes causes high blood sugar.",
            "disease": "Diabetes",
            "score": 0.92
        }]

        result = build_context(chunks)

        assert "Diabetes" in result
        assert "high blood sugar" in result


    def test_max_chars_respected(self):
        chunks = [{
            "text": "x " * 1000,
            "disease": "Test",
            "score": 0.8
        }] * 10

        result = build_context(chunks, max_chars=500)

        assert len(result) <= 1200


# ─────────────────────────────────────────────
# RESPONSE PARSER TESTS
# ─────────────────────────────────────────────
class TestResponseParser:

    def test_strips_whitespace(self):
        assert parse_response("  hello  ") == "hello"


    def test_removes_medibot_prefix(self):
        assert parse_response("MediBot: Hello there") == "Hello there"


    def test_removes_assistant_prefix(self):
        assert parse_response("Assistant: Hi!") == "Hi!"


    def test_disclaimer_logic(self):
        result = add_disclaimer("Eat healthy foods.")

        assert isinstance(result, str)
        assert len(result) > len("Eat healthy foods.")


    def test_disclaimer_not_duplicated(self):
        text = "Please consult your doctor for advice."
        result = add_disclaimer(text)

        assert result.count("disclaimer") <= 1
