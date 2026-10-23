from typing_extensions import TypedDict

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.config import settings
from app.services.knowledge_base import KnowledgeBase
from app.services.retriever import Retriever

router = APIRouter()

HTTP_403_FORBIDDEN = 403
ADMIN_HEADER_NAME = "X-Admin-Key"
FORBIDDEN_DETAIL = "Forbidden: Invalid admin key"
RELOADED_KEY = "reloaded"
RECORDS_KEY = "records"

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


class ReloadResponse(TypedDict):
    reloaded: bool
    records: int


@router.post("/api/v1/admin/reload")
def reload_knowledge_base(
    x_admin_key: str | None = Header(default=None, alias=ADMIN_HEADER_NAME),
    knowledge_base: KnowledgeBase = Depends(get_knowledge_base),
    retriever: Retriever = Depends(get_retriever),
) -> ReloadResponse:
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=FORBIDDEN_DETAIL)

    knowledge_base.reload()
    retriever.rebuild()
    return {
        RELOADED_KEY: True,
        RECORDS_KEY: len(knowledge_base.records),
    }
