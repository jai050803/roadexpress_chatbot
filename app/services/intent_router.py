import re

from app.models.chat import ChatResponse, Department, ResponseStatus
from app.services.knowledge_base import KnowledgeBase
from app.services.response_builder import resolve_department
from app.services.session_manager import SessionState

GREETING_TOKENS: frozenset[str] = frozenset({
    "hi",
    "hello",
    "hey",
    "namaste",
    "pranam",
    "good morning",
    "good afternoon",
    "good evening",
    "greetings",
    "kaise ho",
    "help",
    "start",
    "namaskar",
})

DEPARTMENT_TERMS: dict[Department, tuple[str, ...]] = {
    Department.FINANCE: (
        "finance",
        "finance department",
        "finance team",
        "accounts",
        "accounts department",
        "payouts",
    ),
    Department.OPERATIONS: (
        "operations",
        "ops",
        "operations department",
        "operations team",
        "ops team",
    ),
    Department.SUPPLY: (
        "supply",
        "supply department",
        "supply team",
    ),
    Department.SALES: (
        "sales",
        "sales department",
        "sales team",
    ),
}

INTENT_GREETING = "GREETING"
INTENT_DEPARTMENT_ROUTING = "DEPARTMENT_ROUTING"
GREETING_CONFIDENCE = 1.0
MAX_FOLLOWUP_WORDS = 4

GREETING_RESPONSE_MESSAGE = (
    "Hello! Welcome to Road Express support. I can assist you with live tracking, "
    "POD submissions, freight advance and balance payouts, detention claims, and carrier onboarding. "
    "How can I help you today?"
)

FINANCE_DESK_MESSAGE = (
    "You are connected with the Finance desk. For freight advance, balance settlement, "
    "or deduction queries, please provide your LR number or contact [FINANCE CONTACT]."
)

OPERATIONS_DESK_MESSAGE = (
    "You are connected with the Operations desk. For vehicle tracking, loading/unloading delays, "
    "or detention claims, please provide your vehicle number or contact [OPERATIONS CONTACT]."
)

SUPPLY_DESK_MESSAGE = (
    "You are connected with the Supply desk. For transporter onboarding, vehicle attachment, "
    "and KYC document approval, please contact [SUPPLY CONTACT]."
)

SALES_DESK_MESSAGE = (
    "You are connected with the Sales desk. For enterprise freight contracts and corridor inquiries, "
    "please contact [SALES CONTACT]."
)

PUNCTUATION_REGEX = r"[^\w\s]"


def is_greeting(message: str) -> bool:
    cleaned = re.sub(PUNCTUATION_REGEX, "", message).strip().lower()
    return cleaned in GREETING_TOKENS


def build_greeting_response(session_id: str | None) -> ChatResponse:
    return ChatResponse(
        answer=GREETING_RESPONSE_MESSAGE,
        status=ResponseStatus.ANSWERED,
        intent=INTENT_GREETING,
        department=None,
        faq_id=None,
        confidence=GREETING_CONFIDENCE,
        session_id=session_id,
    )


def extract_department(message: str) -> Department:
    direct = resolve_department(message)
    if direct != Department.UNKNOWN:
        return direct

    cleaned = re.sub(PUNCTUATION_REGEX, "", message).strip().lower()
    for dept, terms in DEPARTMENT_TERMS.items():
        for term in terms:
            if (
                cleaned == term
                or cleaned == f"to {term}"
                or cleaned == f"connect {term}"
                or cleaned == f"connect to {term}"
            ):
                return dept

    return Department.UNKNOWN


def handle_department_followup(
    message: str,
    session: SessionState | None,
    knowledge_base: KnowledgeBase,
) -> ChatResponse | None:
    dept = extract_department(message)
    if dept == Department.UNKNOWN:
        return None

    words = message.strip().split()
    is_short_phrase = len(words) <= MAX_FOLLOWUP_WORDS
    is_awaiting = session is not None and session.awaiting_department

    if not is_short_phrase and not is_awaiting:
        return None

    session_id = session.session_id if session is not None else None

    if session is not None and session.candidate_faq_ids:
        for faq_id in session.candidate_faq_ids:
            record = knowledge_base.get_by_id(faq_id)
            if record is not None and resolve_department(record["department"]) == dept:
                return ChatResponse(
                    answer=record["answer"],
                    status=ResponseStatus.ANSWERED,
                    intent=record["category"],
                    department=dept,
                    faq_id=record["faq_id"],
                    confidence=GREETING_CONFIDENCE,
                    session_id=session_id,
                )

    desk_messages: dict[Department, str] = {
        Department.FINANCE: FINANCE_DESK_MESSAGE,
        Department.OPERATIONS: OPERATIONS_DESK_MESSAGE,
        Department.SUPPLY: SUPPLY_DESK_MESSAGE,
        Department.SALES: SALES_DESK_MESSAGE,
    }

    message_text = desk_messages.get(dept, GREETING_RESPONSE_MESSAGE)
    return ChatResponse(
        answer=message_text,
        status=ResponseStatus.ANSWERED,
        intent=INTENT_DEPARTMENT_ROUTING,
        department=dept,
        faq_id=None,
        confidence=GREETING_CONFIDENCE,
        session_id=session_id,
    )
