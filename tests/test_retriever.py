from pathlib import Path

import pytest

from app.services.knowledge_base import KnowledgeBase
from app.services.retriever import RetrievalResult, Retriever

CSV_HEADER = "faq_id,category,question,alternate_questions,answer,department,status,requires_live_data\n"

FAQ_ID_POD = "FAQ_POD_01"
FAQ_ID_ADV = "FAQ_ADV_01"

QUESTION_POD = "How do I submit the hard copy of the POD?"
ALT_POD_1 = "physical pod submission process"
ALT_POD_2 = "hard copy pod kahan bhejna hai"
ANSWER_POD = "Submit the original signed and stamped physical POD at the nearest branch."

QUESTION_ADV = "When and how is the trip advance payment processed?"
ALT_ADV_1 = "advance payment kab milega"
ALT_ADV_2 = "trip advance payment rules"
ANSWER_ADV = "Trip advance is transferred directly to the registered fleet owner bank account."

TWO_RECORDS_CSV = (
    CSV_HEADER
    + f"{FAQ_ID_POD},POD,{QUESTION_POD},{ALT_POD_1}|{ALT_POD_2},{ANSWER_POD},OPERATIONS,APPROVED,NO\n"
    + f"{FAQ_ID_ADV},ADVANCE,{QUESTION_ADV},{ALT_ADV_1}|{ALT_ADV_2},{ANSWER_ADV},FINANCE,APPROVED,NO\n"
)

HEADER_ONLY_CSV = CSV_HEADER

QUERY_SIMILAR_POD = "Where do I send the original paper POD?"
QUERY_DEDUPLICATION = "submit POD hard copy"

TOP_K_COUNT = 3
TOP_K_DEDUPLICATION = 5
EXPECTED_ZERO_COUNT = 0
EXPECTED_SINGLE_OCCURRENCE = 1
FILE_ENCODING = "utf-8"
FAQ_FILENAME = "test_faq.csv"
EMPTY_FAQ_FILENAME = "empty_faq.csv"


@pytest.fixture
def mock_knowledge_base(tmp_path: Path) -> KnowledgeBase:
    csv_file = tmp_path / FAQ_FILENAME
    csv_file.write_text(TWO_RECORDS_CSV, encoding=FILE_ENCODING)
    return KnowledgeBase(str(csv_file))


@pytest.fixture
def empty_knowledge_base(tmp_path: Path) -> KnowledgeBase:
    csv_file = tmp_path / EMPTY_FAQ_FILENAME
    csv_file.write_text(HEADER_ONLY_CSV, encoding=FILE_ENCODING)
    return KnowledgeBase(str(csv_file))


@pytest.fixture
def retriever_instance(mock_knowledge_base: KnowledgeBase) -> Retriever:
    return Retriever(mock_knowledge_base)


@pytest.fixture
def empty_retriever_instance(empty_knowledge_base: KnowledgeBase) -> Retriever:
    return Retriever(empty_knowledge_base)


def test_search_returns_retrieval_result(retriever_instance: Retriever) -> None:
    results = retriever_instance.search(QUESTION_POD, top_k=TOP_K_COUNT)
    assert len(results) > EXPECTED_ZERO_COUNT
    assert isinstance(results[0], RetrievalResult)
    assert results[0].faq_id == FAQ_ID_POD


def test_search_semantic_similarity_returns_correct_faq_id(retriever_instance: Retriever) -> None:
    results = retriever_instance.search(QUERY_SIMILAR_POD, top_k=TOP_K_COUNT)
    assert len(results) > EXPECTED_ZERO_COUNT
    assert results[0].faq_id == FAQ_ID_POD


def test_search_empty_index_returns_empty_list(empty_retriever_instance: Retriever) -> None:
    results = empty_retriever_instance.search(QUESTION_POD, top_k=TOP_K_COUNT)
    assert results == []


def test_results_deduplicated_by_faq_id(retriever_instance: Retriever) -> None:
    results = retriever_instance.search(QUERY_DEDUPLICATION, top_k=TOP_K_DEDUPLICATION)
    assert len(results) > EXPECTED_ZERO_COUNT
    faq_ids = [result.faq_id for result in results]
    assert len(faq_ids) == len(set(faq_ids))
    assert faq_ids.count(FAQ_ID_POD) == EXPECTED_SINGLE_OCCURRENCE
