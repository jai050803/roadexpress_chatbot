from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.logging import RequestLoggingMiddleware
from app.routes.admin import router as admin_router
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.services.knowledge_base import KnowledgeBase
from app.services.retriever import Retriever

logger = logging.getLogger(__name__)

APP_TITLE = "Road Express Chatbot API"
APP_VERSION = "0.1.0"
ALL_WILDCARD = "*"
LOG_KB_LOADED = "Knowledge base loaded: %d records"
LOG_INDEX_BUILT = "Retriever index built: %d vectors"
LOG_SHUTDOWN = "Shutting down"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    knowledge_base = KnowledgeBase(settings.FAQ_CSV_PATH)
    retriever = Retriever(knowledge_base)
    app.state.knowledge_base = knowledge_base
    app.state.retriever = retriever
    logger.info(LOG_KB_LOADED, len(knowledge_base.records))
    logger.info(LOG_INDEX_BUILT, len(retriever._index_to_faq_id))
    yield
    logger.info(LOG_SHUTDOWN)


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALL_WILDCARD],
    allow_credentials=True,
    allow_methods=[ALL_WILDCARD],
    allow_headers=[ALL_WILDCARD],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(admin_router)
