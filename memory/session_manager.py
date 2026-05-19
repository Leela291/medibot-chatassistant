# memory/session_manager.py
"""Manages multiple chat sessions by session_id."""
import uuid
from memory.conversation_memory import ConversationMemory
from memory.patient_memory import PatientProfile


class Session:
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.memory     = ConversationMemory()
        self.patient    = PatientProfile()

    def reset(self):
        self.memory.clear()
        self.patient = PatientProfile()


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, session_id: str | None = None) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        session = Session(session_id)
        self._sessions[session.session_id] = session
        return session

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def active_sessions(self) -> list[str]:
        return list(self._sessions.keys())


# Global singleton
session_manager = SessionManager()
