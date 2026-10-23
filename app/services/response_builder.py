from app.config import settings
from app.models.chat import ChatResponse, Department, ResponseStatus
from app.services.knowledge_base import FAQRecord
from app.services.retriever import RetrievalResult

NO_MATCH_MESSAGE = (
    "I could not find a verified answer for this question. "
    "Please rephrase your query or contact the relevant department directly."
)

LOW_CONFIDENCE_MESSAGE = (
    "I found a related topic but I am not confident it answers your question. "
    "Could you rephrase, or let me know which department you need help with?"
)

LIVE_DATA_MESSAGE = (
    "This question requires looking up your specific account or shipment details. "
    "Please contact the relevant department with your LR number or truck number."
)

CONFIDENCE_ZERO = 0.0


def resolve_department(department_str: str) -> Department:
    cleaned = department_str.strip().upper()
    for dept in Department:
        if dept.value == cleaned:
            return dept
    return Department.UNKNOWN


def build_response(
    results: list[RetrievalResult],
    session_id: str | None,
) -> ChatResponse:
    if not results:
        return ChatResponse(
            answer=NO_MATCH_MESSAGE,
            status=ResponseStatus.NO_MATCH,
            intent=None,
            department=None,
            faq_id=None,
            confidence=CONFIDENCE_ZERO,
            session_id=session_id,
        )

    top_result = results[0]
    score = top_result.score
    record: FAQRecord = top_result.record

    if score >= settings.HIGH_CONFIDENCE_THRESHOLD:
        if record["requires_live_data"]:
            return ChatResponse(
                answer=LIVE_DATA_MESSAGE,
                status=ResponseStatus.REQUIRES_LIVE_DATA,
                intent=record["category"],
                department=resolve_department(record["department"]),
                faq_id=record["faq_id"],
                confidence=score,
                session_id=session_id,
            )
        return ChatResponse(
            answer=record["answer"],
            status=ResponseStatus.ANSWERED,
            intent=record["category"],
            department=resolve_department(record["department"]),
            faq_id=record["faq_id"],
            confidence=score,
            session_id=session_id,
        )

    if score >= settings.LOW_CONFIDENCE_THRESHOLD:
        return ChatResponse(
            answer=LOW_CONFIDENCE_MESSAGE,
            status=ResponseStatus.LOW_CONFIDENCE,
            intent=record["category"],
            department=resolve_department(record["department"]),
            faq_id=record["faq_id"],
            confidence=score,
            session_id=session_id,
        )

    return ChatResponse(
        answer=NO_MATCH_MESSAGE,
        status=ResponseStatus.NO_MATCH,
        intent=None,
        department=None,
        faq_id=None,
        confidence=CONFIDENCE_ZERO,
        session_id=session_id,
    )
