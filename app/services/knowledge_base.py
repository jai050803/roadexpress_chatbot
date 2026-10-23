import logging
from pathlib import Path
from typing import TypedDict

import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)

STATUS_APPROVED = "APPROVED"
STATUS_DRAFT = "DRAFT"
STATUS_IN_REVIEW = "IN_REVIEW"
STATUS_RETIRED = "RETIRED"

RECOGNIZED_STATUSES: frozenset[str] = frozenset({
    STATUS_APPROVED,
    STATUS_DRAFT,
    STATUS_IN_REVIEW,
    STATUS_RETIRED,
})

COLUMN_FAQ_ID = "faq_id"
COLUMN_CATEGORY = "category"
COLUMN_QUESTION = "question"
COLUMN_ALTERNATE_QUESTIONS = "alternate_questions"
COLUMN_ANSWER = "answer"
COLUMN_ANSWER_EN = "answer_en"
COLUMN_ANSWER_HI = "answer_hi"
COLUMN_ANSWER_HINGLISH = "answer_hinglish"
COLUMN_TAGS = "tags"
COLUMN_DEPARTMENT = "department"
COLUMN_STATUS = "status"
COLUMN_REQUIRES_LIVE_DATA = "requires_live_data"

REQUIRED_COLUMNS: frozenset[str] = frozenset({
    COLUMN_FAQ_ID,
    COLUMN_CATEGORY,
    COLUMN_QUESTION,
    COLUMN_ALTERNATE_QUESTIONS,
    COLUMN_ANSWER,
    COLUMN_DEPARTMENT,
    COLUMN_STATUS,
    COLUMN_REQUIRES_LIVE_DATA,
})

PIPE_DELIMITER = "|"
TRUE_STRINGS: frozenset[str] = frozenset({"true", "1", "yes"})


class FAQRecord(TypedDict):
    faq_id: str
    category: str
    question: str
    alternate_questions: list[str]
    answer: str
    answer_en: str
    answer_hi: str
    answer_hinglish: str
    department: str
    status: str
    requires_live_data: bool
    tags: str


class KnowledgeBase:
    def __init__(self, csv_path: str = settings.FAQ_CSV_PATH) -> None:
        self.csv_path: str = csv_path
        self.records: list[FAQRecord] = []
        self._load()

    def _validate_approved_records(self, df: pd.DataFrame) -> None:
        for _, row in df.iterrows():
            status = str(row[COLUMN_STATUS]).strip() if pd.notna(row[COLUMN_STATUS]) else ""
            if status not in RECOGNIZED_STATUSES:
                logger.warning("Unrecognized status value: %s", status)

            if status != STATUS_APPROVED:
                continue

            faq_id = str(row[COLUMN_FAQ_ID]).strip() if pd.notna(row[COLUMN_FAQ_ID]) else ""
            if not faq_id:
                raise ValueError("Approved row has empty or whitespace faq_id")

            answer = str(row[COLUMN_ANSWER]).strip() if pd.notna(row[COLUMN_ANSWER]) else ""
            if not answer:
                raise ValueError(f"Approved row with faq_id '{faq_id}' has empty or whitespace answer")

    def _load(self) -> None:
        if not Path(self.csv_path).exists():
            raise FileNotFoundError(f"FAQ CSV file not found: {self.csv_path}")

        df = pd.read_csv(self.csv_path)

        if COLUMN_FAQ_ID not in df.columns and "id" in df.columns:
            df[COLUMN_FAQ_ID] = df["id"]
        if COLUMN_ANSWER not in df.columns and COLUMN_ANSWER_EN in df.columns:
            df[COLUMN_ANSWER] = df[COLUMN_ANSWER_EN]

        missing_columns = REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

        self._validate_approved_records(df)

        loaded_records: list[FAQRecord] = []
        for _, row in df.iterrows():
            status = str(row[COLUMN_STATUS]).strip() if pd.notna(row[COLUMN_STATUS]) else ""
            if status != STATUS_APPROVED:
                continue

            alt_raw = row[COLUMN_ALTERNATE_QUESTIONS]
            alternate_questions: list[str] = (
                [q.strip() for q in str(alt_raw).split(PIPE_DELIMITER) if q.strip()]
                if pd.notna(alt_raw)
                else []
            )

            req_live_raw = row[COLUMN_REQUIRES_LIVE_DATA]
            requires_live: bool = (
                bool(req_live_raw)
                if isinstance(req_live_raw, bool)
                else str(req_live_raw).strip().lower() in TRUE_STRINGS
            )

            ans_raw = str(row[COLUMN_ANSWER]).strip()
            ans_en = (
                str(row[COLUMN_ANSWER_EN]).strip()
                if COLUMN_ANSWER_EN in row and pd.notna(row[COLUMN_ANSWER_EN])
                else ans_raw
            )
            ans_hi = (
                str(row[COLUMN_ANSWER_HI]).strip()
                if COLUMN_ANSWER_HI in row and pd.notna(row[COLUMN_ANSWER_HI])
                else ""
            )
            ans_hinglish = (
                str(row[COLUMN_ANSWER_HINGLISH]).strip()
                if COLUMN_ANSWER_HINGLISH in row and pd.notna(row[COLUMN_ANSWER_HINGLISH])
                else ""
            )
            tags = (
                str(row[COLUMN_TAGS]).strip()
                if COLUMN_TAGS in row and pd.notna(row[COLUMN_TAGS])
                else ""
            )

            record: FAQRecord = {
                "faq_id": str(row[COLUMN_FAQ_ID]).strip(),
                "category": str(row[COLUMN_CATEGORY]).strip() if pd.notna(row[COLUMN_CATEGORY]) else "",
                "question": str(row[COLUMN_QUESTION]).strip() if pd.notna(row[COLUMN_QUESTION]) else "",
                "alternate_questions": alternate_questions,
                "answer": ans_raw,
                "answer_en": ans_en,
                "answer_hi": ans_hi,
                "answer_hinglish": ans_hinglish,
                "department": str(row[COLUMN_DEPARTMENT]).strip() if pd.notna(row[COLUMN_DEPARTMENT]) else "",
                "status": status,
                "requires_live_data": requires_live,
                "tags": tags,
            }
            loaded_records.append(record)

        self.records = loaded_records

    def reload(self) -> None:
        self._load()

    def all_questions_for_embedding(self) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for record in self.records:
            faq_id = record["faq_id"]
            if record["question"]:
                pairs.append((record["question"], faq_id))
            for alt_question in record["alternate_questions"]:
                if alt_question:
                    pairs.append((alt_question, faq_id))
        return pairs

    def get_by_id(self, faq_id: str) -> FAQRecord | None:
        for record in self.records:
            if record["faq_id"] == faq_id:
                return record
        return None
