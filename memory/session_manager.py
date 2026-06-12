# memory/session_manager.py
"""Manages multiple chat sessions by session_id."""

import os
import json
import uuid
import time
from memory.conversation_memory import ConversationMemory
from memory.patient_memory import PatientProfile

SESSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sessions"))

class Session:
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.memory     = ConversationMemory()
        self.patient    = PatientProfile()
        self.created_at = time.time()
        self.updated_at = time.time()

    def reset(self):
        self.memory.clear()
        self.patient = PatientProfile()
        self.updated_at = time.time()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "history": self.memory.get_all_history(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        s = cls(data["session_id"])
        s.created_at = data.get("created_at", time.time())
        s.updated_at = data.get("updated_at", time.time())
        s.memory._history = data.get("history", [])
        return s

class SessionManager:
    def __init__(self, storage_dir: str = SESSIONS_DIR):
        self.storage_dir = storage_dir
        self._sessions: dict[str, Session] = {}
        os.makedirs(self.storage_dir, exist_ok=True)
        self._load_all_from_disk()

    def _load_all_from_disk(self):
        """Scan sessions directory and load saved files."""
        if not os.path.exists(self.storage_dir):
            return
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.storage_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        session = Session.from_dict(data)
                        self._sessions[session.session_id] = session
                except Exception as e:
                    print(f"[SessionManager Warning] Failed to load {filename}: {e}")

    def save_session(self, session: Session) -> None:
        """Serialize session to disk."""
        session.updated_at = time.time()
        path = os.path.join(self.storage_dir, f"{session.session_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[SessionManager Error] Failed to save session {session.session_id}: {e}")

    def get_or_create(self, session_id: str | None = None) -> Session:
        if session_id:
            # Check in memory
            if session_id in self._sessions:
                return self._sessions[session_id]
            # Try lazy load from disk
            path = os.path.join(self.storage_dir, f"{session_id}.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        session = Session.from_dict(data)
                        self._sessions[session.session_id] = session
                        return session
                except Exception:
                    pass

        # Create a new one
        session = Session(session_id)
        self._sessions[session.session_id] = session
        self.save_session(session)
        return session

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        path = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"[SessionManager Error] Failed to delete session file: {e}")

    def active_sessions(self) -> list[str]:
        return list(self._sessions.keys())


# Global singleton
session_manager = SessionManager()
