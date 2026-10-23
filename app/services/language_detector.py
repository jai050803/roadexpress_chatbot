import re

DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

HINGLISH_KEYWORDS: frozenset[str] = frozenset({
    "kya", "kab", "kahan", "kaise", "kyun", "kyu", "hai", "hain", "hoga", "hogi",
    "aayega", "aayegi", "milega", "milegi", "mera", "meri", "mere",
    "nahi", "nhi", "na", "gadi", "gaadi", "truck", "maal", "paise", "paisa",
    "bhejo", "bhejna", "karo", "karna", "chahiye", "kitna", "kitne", "kitni",
    "baad", "pehle", "bhi", "toh", "to", "pe", "se", "ko", "me", "mein",
    "bhai", "batao", "bataiye", "dega", "denge", "chal", "chalu", "ruk", "roka",
    "katoti", "bhada", "bilty", "munshiana", "khali", "khaali", "uthana",
    "utar", "kanta", "parchi", "nag", "dalo", "daalo", "apna", "apni",
})

ENGLISH_KEYWORDS: frozenset[str] = frozenset({
    "what", "when", "where", "how", "why", "is", "are", "will", "can", "could",
    "my", "the", "please", "truck", "vehicle", "shipment", "payment", "freight",
    "advance", "balance", "charges", "detention", "damage", "office", "status",
    "tracking", "reach", "destination", "delivery", "receipt", "account",
    "tell", "about", "provide", "services", "book", "rules", "carry",
})

LANG_HI = "hi"
LANG_HINGLISH = "hinglish"
LANG_EN = "en"


def detect_language(text: str) -> str:
    if DEVANAGARI_REGEX.search(text):
        return LANG_HI

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not words:
        return LANG_EN

    hinglish_matches = sum(1 for w in words if w in HINGLISH_KEYWORDS)
    english_matches = sum(1 for w in words if w in ENGLISH_KEYWORDS)

    if hinglish_matches > english_matches or (hinglish_matches > 0 and english_matches == 0):
        return LANG_HINGLISH

    return LANG_EN
