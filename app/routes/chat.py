from typing_extensions import TypedDict

from fastapi import APIRouter, Depends, Request

from app.models.chat import ChatRequest, ChatResponse, FeedbackRequest
from app.services.feedback import log_feedback
from app.services.knowledge_base import KnowledgeBase
from app.services.response_builder import build_response
from app.services.retriever import Retriever

router = APIRouter()

SEARCH_TOP_K = 3

FAQ_ID_KEY = "faq_id"
CATEGORY_KEY = "category"
QUESTION_KEY = "question"
DEPARTMENT_KEY = "department"
RECEIVED_KEY = "received"

_knowledge_base: KnowledgeBase | None = None
_retriever: Retriever | None = None


def set_dependencies(knowledge_base: KnowledgeBase, retriever: Retriever) -> None:
    global _knowledge_base, _retriever
    _knowledge_base = knowledge_base
    _retriever = retriever


def get_knowledge_base(request: Request) -> KnowledgeBase:
    if hasattr(request.app.state, "knowledge_base"):
        return request.app.state.knowledge_base
    if _knowledge_base is not None:
        return _knowledge_base
    raise RuntimeError("KnowledgeBase is not initialized")


def get_retriever(request: Request) -> Retriever:
    if hasattr(request.app.state, "retriever"):
        return request.app.state.retriever
    if _retriever is not None:
        return _retriever
    raise RuntimeError("Retriever is not initialized")


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
    results = retriever.search(request.message, top_k=SEARCH_TOP_K)
    return build_response(results, request.session_id)


@router.post("/api/v1/feedback")
def submit_feedback(
    request: FeedbackRequest,
    knowledge_base: KnowledgeBase = Depends(get_knowledge_base),
    retriever: Retriever = Depends(get_retriever),
) -> FeedbackResponse:
    log_feedback(request)
    return {RECEIVED_KEY: True}
