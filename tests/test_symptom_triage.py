# tests/test_symptom_triage.py
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.symptom_detector import (
    detect_symptom,
    is_informational_query,
    is_vague_symptom_report,
    should_start_triage,
)
from services.triage_questions import get_questions
from tools.wikipedia_tool import extract_wikipedia_queries, get_wikipedia_context


class TestSymptomTriage:
    def test_detects_fever_in_sentence(self):
        assert detect_symptom("I have fever and feel weak") == "fever"

    def test_informational_skips_triage(self):
        assert is_informational_query("What are the symptoms of diabetes?")
        needs, key = should_start_triage("What are the symptoms of diabetes?")
        assert needs is False

    def test_vague_report_starts_general_triage(self):
        needs, key = should_start_triage("I feel sick and don't know what's wrong")
        assert needs is True
        assert key == "general"
        assert len(get_questions("general")) >= 4

    def test_chest_pain_specific_triage(self):
        needs, key = should_start_triage("I have chest pain since morning")
        assert needs is True
        assert key == "chest pain"

    def test_skip_after_questionnaire(self):
        needs, _ = should_start_triage(
            "How long have you had the fever?: 1-3 days",
            skip_detection=True,
        )
        assert needs is False


class TestWikipediaExtraction:
    def test_extracts_from_natural_language(self):
        titles = extract_wikipedia_queries("I have fever and cough for 3 days")
        assert "Fever" in titles or "Cough" in titles

    def test_context_for_symptom_sentence(self):
        ctx = get_wikipedia_context("I have fever and cough")
        assert ctx == "" or "Wikipedia" in ctx
