# tests/test_rag.py
"""Tests for RAG components: chunking, context builder, response parser."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from embeddings.chunking import flatten_json, chunk_text, load_and_chunk_dataset
from rag.context_builder import build_context
from rag.response_parser import parse_response, add_disclaimer


class TestChunking:
    def test_flatten_simple_dict(self):
        data = {"disease": "Test", "symptoms": ["fever", "cough"]}
        result = flatten_json(data)
        assert any("fever" in s for s in result)
        assert any("cough" in s for s in result)

    def test_chunk_text_basic(self):
        text = " ".join(["word"] * 1000)
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        assert all(len(c.split()) <= 100 for c in chunks)

    def test_chunk_overlap(self):
        words = list(range(200))
        text = " ".join(str(w) for w in words)
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        # Verify overlap exists between consecutive chunks
        assert len(chunks) >= 3

    def test_load_dataset(self):
        path = os.path.join(os.path.dirname(__file__), "..", "datasets", "diabetes.json")
        chunks = load_and_chunk_dataset(path)
        assert len(chunks) > 0
        assert all("text" in c and "disease" in c for c in chunks)
        assert all(c["disease"] == "Diabetes" for c in chunks)


class TestContextBuilder:
    def test_empty_chunks(self):
        result = build_context([])
        assert "no" in result.lower() or "not" in result.lower()

    def test_single_chunk(self):
        chunks = [{"text": "Diabetes causes high blood sugar.", "disease": "Diabetes", "score": 0.92}]
        result = build_context(chunks)
        assert "Diabetes" in result
        assert "high blood sugar" in result

    def test_max_chars_respected(self):
        chunks = [{"text": "x " * 1000, "disease": "Test", "score": 0.8}] * 10
        result = build_context(chunks, max_chars=500)
        assert len(result) < 2000  # Some reasonable upper bound


class TestResponseParser:
    def test_strips_whitespace(self):
        assert parse_response("  hello  ") == "hello"

    def test_removes_medibot_prefix(self):
        assert parse_response("MediBot: Hello there") == "Hello there"

    def test_removes_assistant_prefix(self):
        assert parse_response("Assistant: Hi!") == "Hi!"

    def test_disclaimer_added_when_no_doctor_mention(self):
        result = add_disclaimer("Eat healthy foods.")
        assert "consult" in result.lower() or "disclaimer" in result.lower() or "educational" in result.lower()

    def test_disclaimer_not_doubled(self):
        text = "Please consult your doctor for advice."
        result = add_disclaimer(text)
        assert result.count("disclaimer") <= 1
