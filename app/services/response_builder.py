from app.config import settings
from app.models.chat import ChatResponse, Department, ResponseStatus
from app.services.knowledge_base import FAQRecord
from app.services.language_detector import LANG_EN, LANG_HI, LANG_HINGLISH
from app.services.retriever import RetrievalResult

NO_MATCH_MESSAGES: dict[str, str] = {
    LANG_EN: (
        "I could not find a verified answer for this question. "
        "Please rephrase your query or contact the relevant department directly."
    ),
    LANG_HI: (
        "मुझे इस प्रश्न के लिए कोई सत्यापित उत्तर नहीं मिला। "
        "कृपया अपना प्रश्न दोबारा लिखें या सीधे संबंधित विभाग से संपर्क करें।"
    ),
    LANG_HINGLISH: (
        "Hume is sawal ke liye koi verified answer nahi mila. "
        "Kripya apna query dubara likhein ya seedha department se baat karein."
    ),
}

LOW_CONFIDENCE_MESSAGES: dict[str, str] = {
    LANG_EN: (
        "I found a related topic but I am not confident it answers your question. "
        "Could you rephrase, or let me know which department you need help with?"
    ),
    LANG_HI: (
        "मुझे इससे मिलता-जुलता विषय मिला है लेकिन यह आपके प्रश्न का पूरा उत्तर नहीं हो सकता। "
        "क्या आप दोबारा लिख सकते हैं, या बता सकते हैं कि आपको किस विभाग से मदद चाहिए?"
    ),
    LANG_HINGLISH: (
        "Hume milta-julta topic mila hai par confirm nahi hai. "
        "Kya aap dubara likh sakte hain, ya batayein kis department se baat karni hai?"
    ),
}

LIVE_DATA_MESSAGES: dict[str, str] = {
    LANG_EN: (
        "This question requires looking up your specific account or shipment details. "
        "Please contact the relevant department with your LR number or truck number."
    ),
    LANG_HI: (
        "इस प्रश्न के लिए आपकी विशिष्ट खाते या शिपमेंट विवरण की जांच आवश्यक है। "
        "कृपया अपने LR नंबर या गाड़ी नंबर के साथ संबंधित विभाग से संपर्क करें।"
    ),
    LANG_HINGLISH: (
        "Is sawal ke liye aapki shipment ya account details check karni hogi. "
        "Kripya apne LR number ya gaadi number ke saath department se baat karein."
    ),
}

NO_MATCH_MESSAGE = NO_MATCH_MESSAGES[LANG_EN]
LOW_CONFIDENCE_MESSAGE = LOW_CONFIDENCE_MESSAGES[LANG_EN]
LIVE_DATA_MESSAGE = LIVE_DATA_MESSAGES[LANG_EN]

CONFIDENCE_ZERO = 0.0


def resolve_department(department_str: str) -> Department:
    cleaned = department_str.strip().upper()
    for dept in Department:
        if dept.value == cleaned:
            return dept
    return Department.UNKNOWN


def select_answer(record: FAQRecord, language: str) -> str:
    if language == LANG_HI and record.get("answer_hi"):
        return record["answer_hi"]
    if language == LANG_HINGLISH and record.get("answer_hinglish"):
        return record["answer_hinglish"]
    if record.get("answer_en"):
        return record["answer_en"]
    return record.get("answer", "")


def build_response(
    results: list[RetrievalResult],
    session_id: str | None,
    language: str = LANG_EN,
) -> ChatResponse:
    no_match_text = NO_MATCH_MESSAGES.get(language, NO_MATCH_MESSAGE)
    low_conf_text = LOW_CONFIDENCE_MESSAGES.get(language, LOW_CONFIDENCE_MESSAGE)
    live_data_text = LIVE_DATA_MESSAGES.get(language, LIVE_DATA_MESSAGE)

    if not results:
        return ChatResponse(
            answer=no_match_text,
            status=ResponseStatus.NO_MATCH,
            intent=None,
            department=None,
            faq_id=None,
            confidence=CONFIDENCE_ZERO,
            session_id=session_id,
        )

    top_result = results[0]
    score = top_result.score
    record: FAQRecord = top_result.record

    if score >= settings.HIGH_CONFIDENCE_THRESHOLD:
        if record["requires_live_data"]:
            return ChatResponse(
                answer=live_data_text,
                status=ResponseStatus.REQUIRES_LIVE_DATA,
                intent=record["category"],
                department=resolve_department(record["department"]),
                faq_id=record["faq_id"],
                confidence=score,
                session_id=session_id,
            )
        return ChatResponse(
            answer=select_answer(record, language),
            status=ResponseStatus.ANSWERED,
            intent=record["category"],
            department=resolve_department(record["department"]),
            faq_id=record["faq_id"],
            confidence=score,
            session_id=session_id,
        )

    if score >= settings.LOW_CONFIDENCE_THRESHOLD:
        return ChatResponse(
            answer=low_conf_text,
            status=ResponseStatus.LOW_CONFIDENCE,
            intent=record["category"],
            department=resolve_department(record["department"]),
            faq_id=record["faq_id"],
            confidence=score,
            session_id=session_id,
        )

    return ChatResponse(
        answer=no_match_text,
        status=ResponseStatus.NO_MATCH,
        intent=None,
        department=None,
        faq_id=None,
        confidence=CONFIDENCE_ZERO,
        session_id=session_id,
    )
