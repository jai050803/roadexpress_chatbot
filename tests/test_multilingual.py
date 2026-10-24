import pytest

from app.models.chat import ResponseStatus
from app.services.knowledge_base import FAQRecord, KnowledgeBase
from app.services.language_detector import (
    LANG_EN,
    LANG_HI,
    LANG_HINGLISH,
    detect_language,
)
from app.services.response_builder import (
    LOW_CONFIDENCE_MESSAGES,
    NO_MATCH_MESSAGES,
    build_response,
    select_answer,
)
from app.services.retriever import RetrievalResult


@pytest.fixture
def sample_faq_record() -> FAQRecord:
    return {
        "faq_id": "RE-001",
        "category": "general",
        "question": "What is RoadExpress?",
        "alternate_questions": ["Tell me about RoadExpress", "रोडएक्सप्रेस क्या है"],
        "answer": "RoadExpress is a tech logistics company.",
        "answer_en": "RoadExpress is a tech logistics company.",
        "answer_hi": "रोडएक्सप्रेस एक टेक लॉजिस्टिक्स कंपनी है।",
        "answer_hinglish": "RoadExpress ek tech logistics company hai.",
        "department": "SALES",
        "status": "APPROVED",
        "requires_live_data": False,
        "tags": "company,general",
    }


def test_detect_language_devanagari() -> None:
    assert detect_language("रोडएक्सप्रेस क्या है?") == LANG_HI
    assert detect_language("मेरी गाड़ी कहाँ पहुँची") == LANG_HI
    assert detect_language("नमस्ते") == LANG_HI


def test_detect_language_hinglish() -> None:
    assert detect_language("advance kab aayega") == LANG_HINGLISH
    assert detect_language("meri gadi khali nahi ho rahi hai") == LANG_HINGLISH
    assert detect_language("bhai track kaise karein") == LANG_HINGLISH


def test_detect_language_english() -> None:
    assert detect_language("Where is my truck?") == LANG_EN
    assert detect_language("How do I book a vehicle?") == LANG_EN
    assert detect_language("What is RoadExpress Freight?") == LANG_EN


def test_select_answer(sample_faq_record: FAQRecord) -> None:
    assert select_answer(sample_faq_record, LANG_EN) == sample_faq_record["answer_en"]
    assert select_answer(sample_faq_record, LANG_HI) == sample_faq_record["answer_hi"]
    assert select_answer(sample_faq_record, LANG_HINGLISH) == sample_faq_record["answer_hinglish"]


def test_select_answer_fallback() -> None:
    partial_record: FAQRecord = {
        "faq_id": "RE-099",
        "category": "test",
        "question": "Test question?",
        "alternate_questions": [],
        "answer": "Default English answer.",
        "answer_en": "Default English answer.",
        "answer_hi": "",
        "answer_hinglish": "",
        "department": "OPERATIONS",
        "status": "APPROVED",
        "requires_live_data": False,
        "tags": "",
    }
    assert select_answer(partial_record, LANG_HI) == "Default English answer."
    assert select_answer(partial_record, LANG_HINGLISH) == "Default English answer."


def test_build_response_multilingual(sample_faq_record: FAQRecord) -> None:
    mock_result = RetrievalResult(
        faq_id=sample_faq_record["faq_id"],
        score=0.95,
        record=sample_faq_record,
    )

    resp_hi = build_response([mock_result], session_id="s1", language=LANG_HI)
    assert resp_hi.status == ResponseStatus.ANSWERED
    assert resp_hi.answer == sample_faq_record["answer_hi"]

    resp_hinglish = build_response([mock_result], session_id="s1", language=LANG_HINGLISH)
    assert resp_hinglish.status == ResponseStatus.ANSWERED
    assert resp_hinglish.answer == sample_faq_record["answer_hinglish"]

    resp_en = build_response([mock_result], session_id="s1", language=LANG_EN)
    assert resp_en.status == ResponseStatus.ANSWERED
    assert resp_en.answer == sample_faq_record["answer_en"]


def test_build_response_no_match_localized() -> None:
    resp_hi = build_response([], session_id="s1", language=LANG_HI)
    assert resp_hi.status == ResponseStatus.NO_MATCH
    assert resp_hi.answer == NO_MATCH_MESSAGES[LANG_HI]

    resp_hinglish = build_response([], session_id="s1", language=LANG_HINGLISH)
    assert resp_hinglish.status == ResponseStatus.NO_MATCH
    assert resp_hinglish.answer == NO_MATCH_MESSAGES[LANG_HINGLISH]


def test_knowledge_base_loads_all_records() -> None:
    kb = KnowledgeBase("data/faq.csv")
    assert len(kb.records) == 320
    record_ids = {r["faq_id"] for r in kb.records}
    assert "RE-001" in record_ids
    assert "RE-040" in record_ids
    assert "RE-041" in record_ids
    assert "RE-080" in record_ids
    assert "RE-081" in record_ids
    assert "RE-160" in record_ids
    assert "RE-161" in record_ids
    assert "RE-240" in record_ids
    assert "RE-241" in record_ids
    assert "RE-320" in record_ids
    re_001 = kb.get_by_id("RE-001")
    assert re_001 is not None
    assert re_001["answer_hi"] != ""
    assert re_001["answer_hinglish"] != ""
    re_080 = kb.get_by_id("RE-080")
    assert re_080 is not None
    assert re_080["answer_hi"] != ""
    assert re_080["answer_hinglish"] != ""
    re_160 = kb.get_by_id("RE-160")
    assert re_160 is not None
    assert re_160["answer_hi"] != ""
    assert re_160["answer_hinglish"] != ""
    re_240 = kb.get_by_id("RE-240")
    assert re_240 is not None
    assert re_240["answer_hi"] != ""
    assert re_240["answer_hinglish"] != ""
    re_320 = kb.get_by_id("RE-320")
    assert re_320 is not None
    assert re_320["answer_hi"] != ""
    assert re_320["answer_hinglish"] != ""
