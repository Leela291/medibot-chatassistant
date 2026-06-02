"""
Tests for emergency detection, doctor search, and appointment tools.
"""

import sys
import os

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import pytest
from tools.emergency_tool import is_emergency, handle_emergency
from tools.doctor_search_tool import search_doctors, format_doctor_list
from tools.appointment_tool import (
    book_appointment,
    format_confirmation,
    cancel_appointment
)


# ─────────────────────────────────────────────
# EMERGENCY TOOL TESTS
# ─────────────────────────────────────────────
class TestEmergencyTool:

    def test_detects_chest_pain(self):
        assert is_emergency("I have chest pain and can't breathe") is True


    def test_detects_stroke(self):
        assert is_emergency("I think I'm having a stroke") is True


    def test_detects_overdose(self):
        assert is_emergency("I took an overdose of pills") is True


    def test_safe_message(self):
        assert is_emergency("What are the symptoms of diabetes?") is False


    def test_handle_emergency_returns_valid_structure(self):
        result = handle_emergency("I'm having a heart attack")

        assert isinstance(result, dict)
        assert result.get("is_emergency") is True
        assert "answer" in result

        # stronger validation
        answer = result["answer"].lower()
        assert "emergency" in answer or "108" in answer or "112" in answer


    def test_handle_safe_returns_none(self):
        result = handle_emergency("Tell me about asthma")
        assert result is None


# ─────────────────────────────────────────────
# DOCTOR SEARCH TESTS
# ─────────────────────────────────────────────
class TestDoctorSearch:

    def test_search_returns_list(self):
        docs = search_doctors("diabetes")
        assert isinstance(docs, list)


    def test_search_with_city(self):
        docs = search_doctors("diabetes", city="Hyderabad")
        assert isinstance(docs, list)


    def test_format_doctor_list_output(self):
        docs = search_doctors("general")
        formatted = format_doctor_list(docs)

        assert isinstance(formatted, str)
        assert len(formatted) > 0


    def test_empty_list_handling(self):
        result = format_doctor_list([])

        assert isinstance(result, str)
        assert (
            "no doctors" in result.lower()
            or "not found" in result.lower()
        )


# ─────────────────────────────────────────────
# APPOINTMENT TOOL TESTS
# ─────────────────────────────────────────────
class TestAppointmentTool:

    def test_book_appointment_structure(self):
        appt = book_appointment(
            patient_name="Ravi Kumar",
            doctor_name="Dr. Priya Sharma",
            date="2026-06-01",
            time_slot="10:00 AM",
            reason="Diabetes follow-up",
        )

        assert isinstance(appt, dict)
        assert appt.get("id") is not None
        assert appt.get("status") == "confirmed"
        assert appt.get("patient") == "Ravi Kumar"


    def test_format_confirmation(self):
        appt = book_appointment(
            "Test Patient",
            "Dr. Test",
            "2026-06-15",
            "11:00 AM"
        )

        conf = format_confirmation(appt)

        assert isinstance(conf, str)
        assert "Booking ID" in conf
        assert "Test Patient" in conf


    def test_cancel_appointment(self):
        appt = book_appointment(
            "Cancel Me",
            "Dr. X",
            "2026-07-01",
            "09:00 AM"
        )

        result = cancel_appointment(appt["id"])
        assert result is True


    def test_cancel_nonexistent(self):
        result = cancel_appointment("NOTEXIST")
        assert result is False
