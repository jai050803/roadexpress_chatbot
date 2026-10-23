import io
from pathlib import Path

import pandas as pd
import pytest

from app.services.knowledge_base import KnowledgeBase

CSV_HEADER = "faq_id,category,question,alternate_questions,answer,department,status,requires_live_data\n"

FAQ_ID_1 = "FAQ_001"
FAQ_ID_2 = "FAQ_002"
FAQ_ID_DRAFT = "FAQ_003"
FAQ_ID_IN_REVIEW = "FAQ_004"

QUESTION_1 = "Where is my POD?"
ALT_QUESTION_1 = "pod status"
ALT_QUESTION_2 = "check pod"
ANSWER_1 = "POD is at the branch office."

QUESTION_2 = "How to claim detention?"
ALT_QUESTION_3 = "detention process"
ANSWER_2 = "Report arrival time immediately."

VALID_CSV_CONTENT = (
    CSV_HEADER
    + f"{FAQ_ID_1},POD,{QUESTION_1},{ALT_QUESTION_1}|{ALT_QUESTION_2},{ANSWER_1},OPERATIONS,APPROVED,NO\n"
    + f"{FAQ_ID_2},DETENTION,{QUESTION_2},{ALT_QUESTION_3},{ANSWER_2},OPERATIONS,APPROVED,NO\n"
)

CSV_MISSING_COLUMN = (
    "faq_id,category,question,answer,department,status,requires_live_data\n"
    + f"{FAQ_ID_1},POD,{QUESTION_1},{ANSWER_1},OPERATIONS,APPROVED,NO\n"
)

CSV_EMPTY_ANSWER = (
    CSV_HEADER
    + f"{FAQ_ID_1},POD,{QUESTION_1},{ALT_QUESTION_1},   ,OPERATIONS,APPROVED,NO\n"
)

CSV_MULTIPLE_STATUSES = (
    CSV_HEADER
    + f"{FAQ_ID_1},POD,{QUESTION_1},{ALT_QUESTION_1},{ANSWER_1},OPERATIONS,APPROVED,NO\n"
    + f"{FAQ_ID_DRAFT},ADVANCE,Advance info?,adv,Pending,FINANCE,DRAFT,NO\n"
    + f"{FAQ_ID_IN_REVIEW},BALANCE,Balance info?,bal,Under review,FINANCE,IN_REVIEW,NO\n"
)

EXPECTED_TWO_RECORDS = 2
EXPECTED_ONE_RECORD = 1
EXPECTED_PAIR_COUNT = 5
VALUE_ERROR_MISSING_COLUMNS_MATCH = "Missing required columns"
VALUE_ERROR_EMPTY_ANSWER_MATCH = "empty or whitespace answer"
MOCK_FILENAME = "mock_faq.csv"

ORIGINAL_READ_CSV = pd.read_csv


def create_kb_with_stream(
    csv_content: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> KnowledgeBase:
    mock_file = tmp_path / MOCK_FILENAME
    mock_file.touch()
    csv_stream = io.StringIO(csv_content)
    monkeypatch.setattr(pd, "read_csv", lambda *args, **kwargs: ORIGINAL_READ_CSV(csv_stream, **kwargs))
    return KnowledgeBase(str(mock_file))


@pytest.fixture
def knowledge_base_instance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> KnowledgeBase:
    return create_kb_with_stream(VALID_CSV_CONTENT, tmp_path, monkeypatch)


def test_valid_csv_loading(knowledge_base_instance: KnowledgeBase) -> None:
    assert len(knowledge_base_instance.records) == EXPECTED_TWO_RECORDS
    assert knowledge_base_instance.records[0]["faq_id"] == FAQ_ID_1
    assert knowledge_base_instance.records[1]["faq_id"] == FAQ_ID_2


def test_missing_required_column_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match=VALUE_ERROR_MISSING_COLUMNS_MATCH):
        create_kb_with_stream(CSV_MISSING_COLUMN, tmp_path, monkeypatch)


def test_approved_row_empty_answer_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match=VALUE_ERROR_EMPTY_ANSWER_MATCH):
        create_kb_with_stream(CSV_EMPTY_ANSWER, tmp_path, monkeypatch)


def test_draft_and_in_review_excluded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kb = create_kb_with_stream(CSV_MULTIPLE_STATUSES, tmp_path, monkeypatch)
    assert len(kb.records) == EXPECTED_ONE_RECORD
    assert kb.records[0]["faq_id"] == FAQ_ID_1


def test_all_questions_for_embedding(knowledge_base_instance: KnowledgeBase) -> None:
    pairs = knowledge_base_instance.all_questions_for_embedding()
    assert len(pairs) == EXPECTED_PAIR_COUNT
    assert (QUESTION_1, FAQ_ID_1) in pairs
    assert (ALT_QUESTION_1, FAQ_ID_1) in pairs
    assert (ALT_QUESTION_2, FAQ_ID_1) in pairs
    assert (QUESTION_2, FAQ_ID_2) in pairs
    assert (ALT_QUESTION_3, FAQ_ID_2) in pairs
