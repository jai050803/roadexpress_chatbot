import json
import logging
import urllib.error
import urllib.request

from app.config import settings

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 2.0
CONTENT_TYPE_HEADER = "Content-Type"
APPLICATION_JSON = "application/json"
GENERATE_ENDPOINT = "/api/generate"

PROMPT_TEMPLATE = (
    "You are a helpful customer support assistant for Road Express logistics. "
    "Politely and warmly answer the user inquiry using ONLY the provided verified fact. "
    "Keep your answer short (1-2 sentences). Do not invent details.\n\n"
    "Verified Fact: {answer}\n"
    "User Query: {query}\n\n"
    "Polite Response:"
)


def humanize_answer(query: str, raw_answer: str) -> str | None:
    if not settings.ENABLE_OLLAMA:
        return None

    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}{GENERATE_ENDPOINT}"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": PROMPT_TEMPLATE.format(answer=raw_answer, query=query),
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={CONTENT_TYPE_HEADER: APPLICATION_JSON},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
            generated = str(result.get("response", "")).strip()
            if generated:
                return generated
    except Exception as exc:
        logger.warning("Ollama humanization skipped: %s", exc)

    return None
