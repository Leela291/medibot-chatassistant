# tools/doctor_search_tool.py
"""
Mock doctor search tool.
In production, connect this to a real hospital/doctor API or database.
"""
import random

MOCK_DOCTORS = [
    {"name": "Dr. Priya Sharma",   "specialty": "General Physician",  "city": "Hyderabad", "rating": 4.8, "available": True},
    {"name": "Dr. Ravi Kumar",     "specialty": "Diabetologist",      "city": "Bangalore",  "rating": 4.7, "available": True},
    {"name": "Dr. Anita Rao",      "specialty": "Pulmonologist",      "city": "Chennai",    "rating": 4.9, "available": False},
    {"name": "Dr. Suresh Patel",   "specialty": "Endocrinologist",    "city": "Mumbai",     "rating": 4.6, "available": True},
    {"name": "Dr. Meera Nair",     "specialty": "General Physician",  "city": "Kochi",      "rating": 4.5, "available": True},
    {"name": "Dr. Arun Mehta",     "specialty": "Cardiologist",       "city": "Delhi",      "rating": 4.9, "available": True},
    {"name": "Dr. Lakshmi Devi",   "specialty": "Allergist",          "city": "Hyderabad",  "rating": 4.7, "available": True},
    {"name": "Dr. Vikram Singh",   "specialty": "Infectious Disease", "city": "Pune",       "rating": 4.8, "available": False},
]

SPECIALTY_MAP = {
    "diabetes":         "Diabetologist",
    "asthma":           "Pulmonologist",
    "thyroid":          "Endocrinologist",
    "hyperthyroidism":  "Endocrinologist",
    "hypothyroidism":   "Endocrinologist",
    "dengue":           "Infectious Disease",
    "heart":            "Cardiologist",
    "allergy":          "Allergist",
    "general":          "General Physician",
}


def search_doctors(
    condition: str = "general",
    city: str | None = None,
    available_only: bool = True,
) -> list[dict]:
    """Return a list of matching mock doctors."""
    specialty = SPECIALTY_MAP.get(condition.lower(), "General Physician")

    results = [
        d for d in MOCK_DOCTORS
        if specialty.lower() in d["specialty"].lower()
        and (not available_only or d["available"])
        and (not city or city.lower() in d["city"].lower())
    ]

    if not results:
        # Fallback: return any available GP
        results = [d for d in MOCK_DOCTORS if d["available"]][:3]

    return results


def format_doctor_list(doctors: list[dict]) -> str:
    if not doctors:
        return "No doctors found matching your criteria."

    lines = ["Here are some doctors I found:\n"]
    for i, doc in enumerate(doctors, 1):
        avail = "✅ Available" if doc["available"] else "❌ Unavailable"
        lines.append(
            f"{i}. **{doc['name']}** — {doc['specialty']}\n"
            f"   📍 {doc['city']}  |  ⭐ {doc['rating']}  |  {avail}"
        )
    lines.append("\n📞 *To book an appointment, contact the clinic directly.*")
    return "\n".join(lines)
