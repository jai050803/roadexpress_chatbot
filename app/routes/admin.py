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


def get_knowledge_base(request: Request) -> KnowledgeBase:
    return request.app.state.knowledge_base


def get_retriever(request: Request) -> Retriever:
    return request.app.state.retriever


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
