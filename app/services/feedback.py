from datetime import datetime, timezone
import json
import logging
from pathlib import Path

from app.config import settings
from app.models.chat import FeedbackRequest

logger = logging.getLogger(__name__)

TIMESTAMP_KEY = "timestamp"
FILE_MODE_APPEND = "a"
FILE_ENCODING = "utf-8"
NEWLINE = "\n"


def log_feedback(request: FeedbackRequest) -> None:
    try:
        entry = request.model_dump()
        entry[TIMESTAMP_KEY] = datetime.now(timezone.utc).isoformat()
        log_path = Path(settings.FEEDBACK_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open(FILE_MODE_APPEND, encoding=FILE_ENCODING) as file:
            file.write(json.dumps(entry) + NEWLINE)
    except Exception as exc:
        logger.error("Failed to append feedback record: %s", exc)
