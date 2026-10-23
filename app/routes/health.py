from typing_extensions import TypedDict

from fastapi import APIRouter

router = APIRouter()

STATUS_KEY = "status"
STATUS_OK = "ok"


class HealthResponse(TypedDict):
    status: str


@router.get("/health")
def health() -> HealthResponse:
    return {STATUS_KEY: STATUS_OK}
