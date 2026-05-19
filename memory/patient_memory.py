# memory/patient_memory.py
"""Stores patient-provided context within a session (age, conditions, medications)."""
from dataclasses import dataclass, field


@dataclass
class PatientProfile:
    name: str = ""
    age: int | None = None
    gender: str = ""
    known_conditions: list[str] = field(default_factory=list)
    current_medications: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)

    def to_context_string(self) -> str:
        parts = []
        if self.name:
            parts.append(f"Patient name: {self.name}")
        if self.age:
            parts.append(f"Age: {self.age}")
        if self.gender:
            parts.append(f"Gender: {self.gender}")
        if self.known_conditions:
            parts.append(f"Known conditions: {', '.join(self.known_conditions)}")
        if self.current_medications:
            parts.append(f"Medications: {', '.join(self.current_medications)}")
        if self.allergies:
            parts.append(f"Allergies: {', '.join(self.allergies)}")
        return "\n".join(parts) if parts else ""

    def update(self, **kwargs):
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)
