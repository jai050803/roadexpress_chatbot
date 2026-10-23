from enum import StrEnum

from pydantic import BaseModel


class ResponseStatus(StrEnum):
    ANSWERED = "ANSWERED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    AMBIGUOUS = "AMBIGUOUS"
    REQUIRES_LIVE_DATA = "REQUIRES_LIVE_DATA"
    NO_MATCH = "NO_MATCH"


class Department(StrEnum):
    FINANCE = "FINANCE"
    SALES = "SALES"
    SUPPLY = "SUPPLY"
    OPERATIONS = "OPERATIONS"
    UNKNOWN = "UNKNOWN"


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    status: ResponseStatus
    intent: str | None = None
    department: Department | None = None
    faq_id: str | None = None
    confidence: float
    session_id: str | None = None


class FeedbackRequest(BaseModel):
    session_id: str | None = None
    faq_id: str | None = None
    helpful: bool
    comment: str | None = None
