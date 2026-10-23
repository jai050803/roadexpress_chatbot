from typing_extensions import TypedDict

from fastapi import APIRouter, Depends, Request

from app.models.chat import ChatRequest, ChatResponse, FeedbackRequest, ResponseStatus
from app.services.feedback import log_feedback
from app.services.intent_router import (
    build_greeting_response,
    handle_department_followup,
    is_greeting,
)
from app.services.knowledge_base import KnowledgeBase
from app.services.llm import humanize_answer
from app.services.response_builder import build_response
from app.services.retriever import Retriever
from app.services.session_manager import session_manager

router = APIRouter()

SEARCH_TOP_K = 3

FAQ_ID_KEY = "faq_id"
CATEGORY_KEY = "category"
QUESTION_KEY = "question"
DEPARTMENT_KEY = "department"
RECEIVED_KEY = "received"


def get_knowledge_base(request: Request) -> KnowledgeBase:
    return request.app.state.knowledge_base


def get_retriever(request: Request) -> Retriever:
    return request.app.state.retriever


class FAQSummary(TypedDict):
    faq_id: str
    category: str
    question: str
    department: str


class FeedbackResponse(TypedDict):
    received: bool


@router.get("/api/v1/faqs")
def get_faqs(
    knowledge_base: KnowledgeBase = Depends(get_knowledge_base),
    retriever: Retriever = Depends(get_retriever),
) -> list[FAQSummary]:
    return [
        {
            FAQ_ID_KEY: record["faq_id"],
            CATEGORY_KEY: record["category"],
            QUESTION_KEY: record["question"],
            DEPARTMENT_KEY: record["department"],
        }
        for record in knowledge_base.records
    ]


@router.post("/api/v1/chat")
def chat(
    request: ChatRequest,
    knowledge_base: KnowledgeBase = Depends(get_knowledge_base),
    retriever: Retriever = Depends(get_retriever),
) -> ChatResponse:
    session = (
        session_manager.get_or_create(request.session_id)
        if request.session_id is not None
        else None
    )

    if is_greeting(request.message):
        if session is not None and request.session_id is not None:
            session_manager.update(
                request.session_id,
                message=request.message,
                status=ResponseStatus.ANSWERED,
                awaiting_department=False,
            )
        return build_greeting_response(request.session_id)

    dept_response = handle_department_followup(
        request.message,
        session,
        knowledge_base,
    )
    if dept_response is not None:
        if session is not None and request.session_id is not None:
            session_manager.update(
                request.session_id,
                message=request.message,
                status=dept_response.status,
                department=dept_response.department,
                awaiting_department=False,
            )
        return dept_response

    results = retriever.search(request.message, top_k=SEARCH_TOP_K)
    response = build_response(results, request.session_id)

    if response.status == ResponseStatus.ANSWERED:
        humanized = humanize_answer(request.message, response.answer)
        if humanized is not None:
            response.answer = humanized

    if session is not None and request.session_id is not None:
        candidate_ids = [r.faq_id for r in results]
        awaiting = response.status == ResponseStatus.LOW_CONFIDENCE
        session_manager.update(
            request.session_id,
            message=request.message,
            faq_id=response.faq_id,
            intent=response.intent,
            status=response.status,
            department=response.department,
            awaiting_department=awaiting,
            candidate_faq_ids=candidate_ids,
        )

    return response


@router.post("/api/v1/feedback")
def submit_feedback(
    request: FeedbackRequest,
    knowledge_base: KnowledgeBase = Depends(get_knowledge_base),
    retriever: Retriever = Depends(get_retriever),
) -> FeedbackResponse:
    log_feedback(request)
    return {RECEIVED_KEY: True}
