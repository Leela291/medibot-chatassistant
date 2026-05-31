"""
Stores and manages the per-session conversation history
and symptom-triage state.
"""

from llm.config import MAX_HISTORY_TURNS


class ConversationMemory:
    """In-memory conversation history with triage support."""

    def __init__(self, max_turns: int = MAX_HISTORY_TURNS):
        self.max_turns = max_turns
        self._history: list[dict] = []

        # New: Symptom assessment state
        self.triage_state = {
            "active": False,
            "primary_symptom": None,
            "questions": [],
            "current_question_index": 0,
            "answers": {},
            "assessment_complete": False,
        }

    # --------------------------------------------------
    # Chat History
    # --------------------------------------------------

    def add_user(self, message: str) -> None:
        self._history.append({
            "role": "user",
            "content": message
        })
        self._trim()

    def add_assistant(self, message: str) -> None:
        self._history.append({
            "role": "assistant",
            "content": message
        })
        self._trim()

    def get_history(self) -> list[dict]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()
        self.reset_triage()

    def _trim(self) -> None:
        max_messages = self.max_turns * 2

        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    def summary(self) -> str:
        lines = []

        for m in self._history:
            role = "You" if m["role"] == "user" else "MediBot"

            text = m["content"]

            if len(text) > 80:
                text = text[:80] + "..."

            lines.append(f"{role}: {text}")

        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._history)

    # --------------------------------------------------
    # Triage Functions
    # --------------------------------------------------

    def start_triage(self, symptom: str, questions: list[str]):
        """
        Start a symptom assessment session.
        """

        self.triage_state = {
            "active": True,
            "primary_symptom": symptom,
            "questions": questions,
            "current_question_index": 0,
            "answers": {},
            "assessment_complete": False,
        }

    def get_current_question(self):
        questions = self.triage_state["questions"]
        idx = self.triage_state["current_question_index"]

        if idx < len(questions):
            return questions[idx]

        return None

    def save_answer(self, answer: str):
        """
        Save answer for current question.
        """

        question = self.get_current_question()

        if question:
            self.triage_state["answers"][question] = answer

        self.triage_state["current_question_index"] += 1

        if (
            self.triage_state["current_question_index"]
            >= len(self.triage_state["questions"])
        ):
            self.triage_state["assessment_complete"] = True

    def reset_triage(self):
        """
        Reset symptom assessment state.
        """

        self.triage_state = {
            "active": False,
            "primary_symptom": None,
            "questions": [],
            "current_question_index": 0,
            "answers": {},
            "assessment_complete": False,
        }

    def get_triage_summary(self):
        """
        Returns collected symptom information.
        """

        symptom = self.triage_state["primary_symptom"]

        answers = self.triage_state["answers"]

        lines = [f"Primary Symptom: {symptom}", ""]

        for q, a in answers.items():
            lines.append(f"{q}: {a}")

        return "\n".join(lines)