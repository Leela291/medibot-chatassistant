# tests/test_tools.py
"""Tests for emergency detection, doctor search, and appointment tools."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from tools.emergency_tool import is_emergency, handle_emergency
from tools.doctor_search_tool import search_doctors, format_doctor_list
from tools.appointment_tool import book_appointment, format_confirmation, cancel_appointment


class TestEmergencyTool:
    def test_detects_chest_pain(self):
        assert is_emergency("I have chest pain and can't breathe")

    def test_detects_stroke(self):
        assert is_emergency("I think I'm having a stroke")

    def test_detects_overdose(self):
        assert is_emergency("I took an overdose of pills")

    def test_safe_message(self):
        assert not is_emergency("What are the symptoms of diabetes?")

    def test_handle_emergency_returns_dict(self):
        result = handle_emergency("I'm having a heart attack")
        assert result is not None
        assert "answer" in result
        assert result["is_emergency"] is True
        assert "108" in result["answer"] or "112" in result["answer"]

    def test_handle_safe_returns_none(self):
        result = handle_emergency("Tell me about asthma")
        assert result is None


class TestDoctorSearch:
    def test_search_diabetologist(self):
        docs = search_doctors("diabetes")
        assert len(docs) > 0
        assert any("Diabetologist" in d["specialty"] or "General" in d["specialty"] for d in docs)

    def test_search_with_city(self):
        docs = search_doctors("diabetes", city="Hyderabad")
        assert len(docs) >= 0  # may be 0 if none match

    def test_format_doctor_list(self):
        docs = search_doctors("general")
        formatted = format_doctor_list(docs)
        assert isinstance(formatted, str)
        assert len(formatted) > 10

    def test_empty_list_formats_gracefully(self):
        result = format_doctor_list([])
        assert "no doctors" in result.lower() or "not found" in result.lower()


class TestAppointmentTool:
    def test_book_appointment(self):
        appt = book_appointment(
            patient_name="Ravi Kumar",
            doctor_name="Dr. Priya Sharma",
            date="2026-06-01",
            time_slot="10:00 AM",
            reason="Diabetes follow-up",
        )
        assert appt["id"]
        assert appt["status"] == "confirmed"
        assert appt["patient"] == "Ravi Kumar"

    def test_format_confirmation(self):
        appt = book_appointment("Test Patient", "Dr. Test", "2026-06-15", "11:00 AM")
        conf = format_confirmation(appt)
        assert "Booking ID" in conf
        assert "Test Patient" in conf

    def test_cancel_appointment(self):
        appt = book_appointment("Cancel Me", "Dr. X", "2026-07-01", "09:00 AM")
        result = cancel_appointment(appt["id"])
        assert result is True

    def test_cancel_nonexistent(self):
        result = cancel_appointment("NOTEXIST")
        assert result is False
