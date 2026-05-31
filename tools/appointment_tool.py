# tools/appointment_tool.py
"""
Mock appointment booking tool.
In production, connect to a real scheduling API.
"""
import uuid
from datetime import datetime, timedelta
import random

# In-memory appointment store
_appointments: dict[str, dict] = {}

AVAILABLE_SLOTS = [
    "09:00 AM", "10:00 AM", "11:00 AM",
    "02:00 PM", "03:00 PM", "04:00 PM",
]


def get_available_slots(doctor_name: str, date: str | None = None) -> list[str]:
    """Return available time slots for a given doctor."""
    # Mock: return random subset of slots
    available = random.sample(AVAILABLE_SLOTS, k=random.randint(2, 5))
    return sorted(available)


def book_appointment(
    patient_name: str,
    doctor_name: str,
    date: str,
    time_slot: str,
    reason: str = "",
) -> dict:
    """Book an appointment and return a confirmation."""
    appointment_id = str(uuid.uuid4())[:8].upper()
    appointment = {
        "id":           appointment_id,
        "patient":      patient_name,
        "doctor":       doctor_name,
        "date":         date,
        "time":         time_slot,
        "reason":       reason,
        "status":       "confirmed",
        "booked_at":    datetime.now().isoformat(),
    }
    _appointments[appointment_id] = appointment
    return appointment


def get_appointment(appointment_id: str) -> dict | None:
    return _appointments.get(appointment_id)


def cancel_appointment(appointment_id: str) -> bool:
    if appointment_id in _appointments:
        _appointments[appointment_id]["status"] = "cancelled"
        return True
    return False


def format_confirmation(appt: dict) -> str:
    return (
        f"✅ **Appointment Confirmed!**\n\n"
        f"🆔 Booking ID: `{appt['id']}`\n"
        f"👤 Patient:    {appt['patient']}\n"
        f"🩺 Doctor:     {appt['doctor']}\n"
        f"📅 Date:       {appt['date']}\n"
        f"🕐 Time:       {appt['time']}\n"
        f"📋 Reason:     {appt.get('reason', 'General consultation')}\n\n"
        f"Please arrive 10 minutes early. Carry valid ID and any previous medical records."
    )
