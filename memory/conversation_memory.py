# memory/conversation_memory.py
"""
Stores and manages the per-session conversation history.
"""
from llm.config import MAX_HISTORY_TURNS


class ConversationMemory:
    """In-memory conversation history with a rolling window."""

    def __init__(self, max_turns: int = MAX_HISTORY_TURNS):
        self.max_turns = max_turns
        self._history: list[dict] = []

    def add_user(self, message: str) -> None:
        self._history.append({"role": "user", "content": message})
        self._trim()

    def add_assistant(self, message: str) -> None:
        self._history.append({"role": "assistant", "content": message})
        self._trim()

    def get_history(self) -> list[dict]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()

    def _trim(self) -> None:
        """Keep only the last max_turns pairs (2 messages per turn)."""
        max_messages = self.max_turns * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    def summary(self) -> str:
        lines = []
        for m in self._history:
            role = "You" if m["role"] == "user" else "MediBot"
            lines.append(f"{role}: {m['content'][:80]}{'...' if len(m['content']) > 80 else ''}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._history)
