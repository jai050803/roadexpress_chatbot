from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading

from app.models.chat import Department, ResponseStatus

DEFAULT_AWAITING_STATE = False


@dataclass
class SessionState:
    session_id: str
    last_message: str | None = None
    last_faq_id: str | None = None
    last_intent: str | None = None
    last_status: ResponseStatus | None = None
    last_department: Department | None = None
    awaiting_department: bool = DEFAULT_AWAITING_STATE
    candidate_faq_ids: list[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str) -> SessionState:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = SessionState(session_id=session_id)
                self._sessions[session_id] = session
            return session

    def update(
        self,
        session_id: str,
        message: str | None = None,
        faq_id: str | None = None,
        intent: str | None = None,
        status: ResponseStatus | None = None,
        department: Department | None = None,
        awaiting_department: bool | None = None,
        candidate_faq_ids: list[str] | None = None,
    ) -> SessionState:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = SessionState(session_id=session_id)
                self._sessions[session_id] = session

            session.updated_at = datetime.now(timezone.utc)
            if message is not None:
                session.last_message = message
            if faq_id is not None:
                session.last_faq_id = faq_id
            if intent is not None:
                session.last_intent = intent
            if status is not None:
                session.last_status = status
            if department is not None:
                session.last_department = department
            if awaiting_department is not None:
                session.awaiting_department = awaiting_department
            if candidate_faq_ids is not None:
                session.candidate_faq_ids = candidate_faq_ids

            return session


session_manager = SessionManager()
