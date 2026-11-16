"""AI planner: RAG-grounded task suggestions with guardrails.

Flow: safety check on the request -> retrieve passages -> prompt Gemini with
the pet profile + passages -> parse JSON -> validate each suggestion -> score
confidence. Any failure (no key, API error, bad JSON, nothing retrieved)
returns a PlanResult with fallback=True so the caller uses the plain
rule-based scheduler instead.

The LLM call is injectable (`llm=`) so tests and the evaluation script can run
without network access.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from pawpal_system import PRIORITY_ORDER, Pet, Task, _time_to_minutes
from retriever import Passage, life_stage, retrieve

try:  # optional: load GEMINI_API_KEY from .env
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

logger = logging.getLogger("pawpal.planner")


def configure_logging(path: str = "pawpal.log") -> None:
    """Log pawpal.* messages to a file (idempotent)."""
    root = logging.getLogger("pawpal")
    if any(isinstance(h, logging.FileHandler) for h in root.handlers):
        return
    handler = logging.FileHandler(path)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


MODEL = os.environ.get("PAWPAL_MODEL", "gemini-3.5-flash-lite")
VALID_FREQUENCIES = {"once", "daily", "weekly"}
MAX_SUGGESTIONS = 5

# Guardrails -----------------------------------------------------------------
# Doses like "5 mg", "2ml", "10 mg/kg" and "half a tablet" must never be suggested.
DOSE_PATTERN = re.compile(
    r"\b\d+(\.\d+)?\s*(mg|mcg|ml|cc|iu|units?|tablets?|pills?|capsules?|drops?)\b"
    r"|\b(half|quarter|one|two|three)\s+(a\s+)?(tablet|pill|capsule)s?\b",
    re.IGNORECASE,
)
# Requests asking the assistant to decide a dose or medication.
DOSE_REQUEST_PATTERN = re.compile(
    r"\b(dose|dosage|dosing|how (much|many) .{0,40}(give|take)|ibuprofen|acetaminophen|"
    r"tylenol|aspirin|advil|prescribe)\b",
    re.IGNORECASE,
)
VET_MESSAGE = (
    "I can't recommend medication or doses. Please contact your veterinarian "
    "or an emergency vet, who can advise based on your pet's weight and health."
)


@dataclass
class Suggestion:
    title: str
    duration: int
    priority: str
    time: str
    frequency: str
    reason: str
    source: str  # passage id the suggestion cites

    def to_task(self) -> Task:
        return Task(self.title, self.duration, self.priority, self.time, self.frequency)


@dataclass
class PlanResult:
    suggestions: List[Suggestion] = field(default_factory=list)
    passages: List[Passage] = field(default_factory=list)
    confidence: float = 0.0
    fallback: bool = False
    blocked: bool = False
    message: str = ""
    rejected: List[str] = field(default_factory=list)  # why items were dropped


# Validation -------------------------------------------------------------------
def check_request_safety(text: str) -> Optional[str]:
    """Return a refusal message if the request asks for medication advice."""
    if text and DOSE_REQUEST_PATTERN.search(text):
        return VET_MESSAGE
    return None


def validate_suggestion(raw: dict, allowed_sources: set) -> Suggestion:
    """Turn one raw dict into a Suggestion or raise ValueError saying why not."""
    if not isinstance(raw, dict):
        raise ValueError("suggestion is not an object")
    title = str(raw.get("title", "")).strip()
    reason = str(raw.get("reason", "")).strip()
    if not title:
        raise ValueError("missing title")
    if not reason:
        raise ValueError(f"'{title}': missing reason")
    try:
        duration = int(raw.get("duration"))
    except (TypeError, ValueError):
        raise ValueError(f"'{title}': duration is not a number")
    if not 1 <= duration <= 240:
        raise ValueError(f"'{title}': duration {duration} outside 1-240")
    priority = str(raw.get("priority", "")).strip().lower()
    if priority not in PRIORITY_ORDER:
        raise ValueError(f"'{title}': invalid priority {priority!r}")
    time = str(raw.get("time", "")).strip()
    try:
        _time_to_minutes(time)
    except ValueError:
        raise ValueError(f"'{title}': invalid time {time!r}")
    frequency = str(raw.get("frequency", "once")).strip().lower()
    if frequency not in VALID_FREQUENCIES:
        raise ValueError(f"'{title}': invalid frequency {frequency!r}")
    source = str(raw.get("source", "")).strip()
    if source not in allowed_sources:
        raise ValueError(f"'{title}': cites unknown source {source!r} (not retrieved)")
    if DOSE_PATTERN.search(title) or DOSE_PATTERN.search(reason):
        raise ValueError(f"'{title}': contains a medication dose (blocked)")
    return Suggestion(title, duration, priority, time, frequency, reason, source)


def parse_response(text: str) -> list:
    """Extract the JSON array from a model reply (tolerates code fences / prose)."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON array in reply")
    data = json.loads(match.group(0))
    if not isinstance(data, list):
        raise ValueError("reply is not a JSON array")
    return data


def compute_confidence(passages: List[Passage], n_valid: int, n_total: int) -> float:
    """0-1 score: 50% retrieval strength, 50% share of suggestions that validated."""
    if not passages or n_total == 0:
        return 0.0
    retrieval = min(passages[0].score / 0.5, 1.0)  # a top score of 0.5+ counts as strong
    validity = n_valid / n_total
    return round(0.5 * retrieval + 0.5 * validity, 2)


# Prompt + LLM -------------------------------------------------------------------
def build_prompt(pet: Pet, passages: List[Passage], existing: List[Task]) -> str:
    stage = life_stage(pet.species, pet.age)
    docs = "\n\n".join(f"[{p.source}]\n{p.text}" for p in passages)
    have = "\n".join(f"- {t.time} {t.title}" for t in existing) or "(none)"
    return f"""You help a pet owner plan care tasks. Use ONLY the reference passages below; do not use outside knowledge.

Pet: {pet.name}, {pet.species}, breed: {pet.breed or 'unknown'}, age: {pet.age} ({stage})

Reference passages (cite by the id in brackets):
{docs}

Tasks already scheduled (do not duplicate these or reuse their times):
{have}

Suggest up to {MAX_SUGGESTIONS} tasks for this pet, grounded in the passages. Never include medication names, doses or amounts.
Reply with ONLY a JSON array. Each item must have:
"title" (string), "duration" (minutes, integer), "priority" ("low"|"medium"|"high"),
"time" ("HH:MM" 24-hour), "frequency" ("once"|"daily"|"weekly"),
"reason" (one sentence explaining how the passage applies to this pet),
"source" (exactly one passage id from above)."""


def api_key() -> Optional[str]:
    """Gemini key from GEMINI_API_KEY (or GOOGLE_API_KEY), if set."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


RETRYABLE_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT_MS = 30_000


def call_gemini(prompt: str, sleep: Callable[[float], None] = time.sleep) -> str:
    """Call Gemini, retrying temporary errors (rate limit / overload) with backoff."""
    from google import genai  # imported lazily so tests don't need a key
    from google.genai import errors, types

    client = genai.Client(
        api_key=api_key(), http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS)
    )
    config = types.GenerateContentConfig(
        response_mime_type="application/json", max_output_tokens=1500, temperature=0.3
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            reply = client.models.generate_content(model=MODEL, contents=prompt, config=config)
            break
        except errors.APIError as exc:
            if exc.code not in RETRYABLE_CODES or attempt == MAX_ATTEMPTS:
                raise
            delay = 2 ** attempt  # 2s, 4s, 8s
            logger.warning("Gemini error %s (attempt %d/%d); retrying in %ds", exc.code, attempt, MAX_ATTEMPTS, delay)
            sleep(delay)
    if not reply.text:
        raise ValueError("empty reply (possibly blocked by safety filters)")
    return reply.text


# Public API -----------------------------------------------------------------------
def suggest_tasks(
    pet: Pet,
    focus: str = "daily care exercise feeding grooming",
    existing: Optional[List[Task]] = None,
    llm: Optional[Callable[[str], str]] = None,
) -> PlanResult:
    """Suggest tasks for a pet, grounded in retrieved care guidance.

    Args:
        pet: the pet (species and age drive retrieval).
        focus: what the owner wants help with (also safety-checked).
        existing: the pet's current tasks, used to avoid duplicates.
        llm: function prompt -> reply text. Defaults to the Gemini API.
    """
    existing = existing or []
    logger.info("suggest_tasks pet=%s species=%s age=%s focus=%r", pet.name, pet.species, pet.age, focus)

    refusal = check_request_safety(focus)
    if refusal:
        logger.warning("Blocked unsafe request: %r", focus)
        return PlanResult(blocked=True, message=refusal)

    passages = retrieve(focus, pet.species, pet.age, top_k=3)
    if not passages:
        logger.warning("No relevant passages; falling back")
        return PlanResult(fallback=True, message="No relevant care guidance found, so no AI suggestions were made.")

    if llm is None:
        if not api_key():
            logger.warning("GEMINI_API_KEY not set; falling back")
            return PlanResult(fallback=True, passages=passages, message="No API key set, so AI suggestions are unavailable.")
        llm = call_gemini

    try:
        raw_items = parse_response(llm(build_prompt(pet, passages, existing)))
    except Exception as exc:  # network, auth, bad JSON: all degrade the same way
        logger.error("LLM step failed: %s", exc)
        return PlanResult(fallback=True, passages=passages, message=f"AI step failed ({type(exc).__name__}); using the standard scheduler.")

    allowed = {p.source for p in passages}
    have_titles = {t.title.strip().lower() for t in existing}
    have_times = {_time_to_minutes(t.time) for t in existing if _is_time(t.time)}
    valid: List[Suggestion] = []
    rejected: List[str] = []
    for raw in raw_items[:MAX_SUGGESTIONS]:
        try:
            s = validate_suggestion(raw, allowed)
            if s.title.lower() in have_titles:
                raise ValueError(f"'{s.title}': duplicates an existing task")
            if _time_to_minutes(s.time) in have_times:
                raise ValueError(f"'{s.title}': time {s.time} conflicts with an existing task")
            valid.append(s)
            have_times.add(_time_to_minutes(s.time))
        except ValueError as exc:
            logger.warning("Rejected suggestion: %s", exc)
            rejected.append(str(exc))

    total = min(len(raw_items), MAX_SUGGESTIONS)
    confidence = compute_confidence(passages, len(valid), total)
    logger.info("Result: %d valid, %d rejected, confidence=%s", len(valid), len(rejected), confidence)
    if not valid:
        return PlanResult(fallback=True, passages=passages, rejected=rejected, message="No AI suggestion passed validation; using the standard scheduler.")
    return PlanResult(suggestions=valid, passages=passages, confidence=confidence, rejected=rejected)


def _is_time(value: str) -> bool:
    try:
        _time_to_minutes(value)
        return True
    except ValueError:
        return False
