from pathlib import Path
import pytest

from app.models.chat import Department, ResponseStatus
from app.services.intent_router import (
    build_greeting_response,
    handle_department_followup,
    is_greeting,
)
from app.services.knowledge_base import KnowledgeBase
from app.services.llm import humanize_answer
from app.services.session_manager import SessionManager, SessionState


SAMPLE_CSV = """faq_id,category,question,alternate_questions,answer,department,requires_live_data,status
FAQ_OPS_01,TRACKING,Where is my vehicle?,gadi kahan hai,Vehicle tracking is live via GPS,OPERATIONS,YES,APPROVED
FAQ_FIN_01,ADVANCE,When will advance come?,advance kab aayega,Advance is paid within 2 hours,FINANCE,NO,APPROVED
"""


@pytest.fixture
def sample_kb(tmp_path: Path) -> KnowledgeBase:
    csv_file = tmp_path / "sample_faq.csv"
    csv_file.write_text(SAMPLE_CSV, encoding="utf-8")
    return KnowledgeBase(str(csv_file))


def test_session_manager_get_or_create_and_update() -> None:
    sm = SessionManager()
    session = sm.get_or_create("sess-1")
    assert session.session_id == "sess-1"
    assert session.awaiting_department is False

    updated = sm.update(
        "sess-1",
        message="delay issues",
        status=ResponseStatus.LOW_CONFIDENCE,
        awaiting_department=True,
        candidate_faq_ids=["FAQ_OPS_01"],
    )
    assert updated.last_message == "delay issues"
    assert updated.awaiting_department is True
    assert updated.candidate_faq_ids == ["FAQ_OPS_01"]


def test_is_greeting() -> None:
    assert is_greeting("hello") is True
    assert is_greeting("Namaste!") is True
    assert is_greeting("Hi ") is True
    assert is_greeting("good morning") is True
    assert is_greeting("where is my truck?") is False
    assert is_greeting("operations") is False


def test_build_greeting_response() -> None:
    resp = build_greeting_response(session_id="sess-abc")
    assert resp.status == ResponseStatus.ANSWERED
    assert resp.intent == "GREETING"
    assert resp.confidence == 1.0
    assert resp.session_id == "sess-abc"
    assert "Road Express" in resp.answer


def test_handle_department_followup_with_matching_candidate(sample_kb: KnowledgeBase) -> None:
    session = SessionState(
        session_id="sess-xyz",
        awaiting_department=True,
        candidate_faq_ids=["FAQ_OPS_01", "FAQ_FIN_01"],
    )
    resp = handle_department_followup("operations", session, sample_kb)
    assert resp is not None
    assert resp.status == ResponseStatus.ANSWERED
    assert resp.faq_id == "FAQ_OPS_01"
    assert resp.department == Department.OPERATIONS


def test_handle_department_followup_direct_routing_without_candidate(sample_kb: KnowledgeBase) -> None:
    session = SessionState(session_id="sess-xyz", awaiting_department=False)
    resp = handle_department_followup("finance department", session, sample_kb)
    assert resp is not None
    assert resp.status == ResponseStatus.ANSWERED
    assert resp.department == Department.FINANCE
    assert resp.faq_id is None
    assert "Finance desk" in resp.answer


def test_handle_department_followup_non_department(sample_kb: KnowledgeBase) -> None:
    session = SessionState(session_id="sess-xyz")
    resp = handle_department_followup("random message", session, sample_kb)
    assert resp is None


def test_humanize_answer_disabled_by_default() -> None:
    result = humanize_answer("hello", "verified answer")
    assert result is None
