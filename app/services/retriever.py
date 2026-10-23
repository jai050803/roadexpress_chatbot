from dataclasses import dataclass
import logging

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.services.knowledge_base import FAQRecord, KnowledgeBase

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 3
EMPTY_VECTOR_COUNT = 0


@dataclass
class RetrievalResult:
    faq_id: str
    score: float
    record: FAQRecord


class Retriever:
    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.knowledge_base: KnowledgeBase = knowledge_base
        self._model: SentenceTransformer = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._index: faiss.IndexFlatIP | None = None
        self._index_to_faq_id: list[str] = []
        self.build_index()

    def build_index(self) -> None:
        pairs = self.knowledge_base.all_questions_for_embedding()
        if not pairs:
            self._index_to_faq_id = []
            self._index = None
            logger.info("Indexed %d vectors into FAISS", EMPTY_VECTOR_COUNT)
            return

        texts = [pair[0] for pair in pairs]
        self._index_to_faq_id = [pair[1] for pair in pairs]

        raw_embeddings = self._model.encode(texts, normalize_embeddings=True)
        embeddings = np.ascontiguousarray(raw_embeddings, dtype=np.float32)

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        self._index = index

        logger.info("Indexed %d vectors into FAISS", len(self._index_to_faq_id))

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[RetrievalResult]:
        if self._index is None or self._index.ntotal == EMPTY_VECTOR_COUNT:
            return []

        search_k = min(top_k, self._index.ntotal)
        query_vector = np.ascontiguousarray(
            self._model.encode([query], normalize_embeddings=True),
            dtype=np.float32,
        )

        scores, indices = self._index.search(query_vector, search_k)

        seen_faq_ids: set[str] = set()
        results: list[RetrievalResult] = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            faq_id = self._index_to_faq_id[idx]
            if faq_id in seen_faq_ids:
                continue

            seen_faq_ids.add(faq_id)
            record = self.knowledge_base.get_by_id(faq_id)
            if record is None:
                continue

            results.append(
                RetrievalResult(
                    faq_id=faq_id,
                    score=float(score),
                    record=record,
                )
            )

        results.sort(key=lambda item: item.score, reverse=True)
        return results

    def rebuild(self) -> None:
        self.build_index()
