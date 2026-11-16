"""Retriever: finds pet-care guidance passages relevant to a pet and task.

Documents live in knowledge/*.md. Each "## " section is one passage. A file may
declare "species: dog" (or cat) on its own line; passages from files for a
different species are excluded, and files with no species apply to all pets.

Scoring is a small TF-IDF over passage words, with a boost when the passage
mentions the pet's life stage (puppy/kitten, adult, senior). No external
dependencies, no vector database: the knowledge base is small by design.
"""

import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("pawpal.retriever")

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
STOPWORDS = {
    "a", "an", "and", "the", "of", "to", "for", "in", "on", "is", "are", "or",
    "with", "as", "at", "by", "be", "it", "that", "this", "can", "from", "up",
}


@dataclass
class Passage:
    source: str  # e.g. "dog_exercise.md#Senior dog exercise"
    heading: str
    text: str
    species: Optional[str]  # None = applies to every species
    score: float = 0.0


def _tokens(text: str) -> List[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def life_stage(species: str, age: int) -> str:
    """Map a pet's age in years to 'young', 'adult' or 'senior'."""
    senior_at = 10 if species.lower() == "cat" else 8
    if age < 1:
        return "young"
    return "senior" if age >= senior_at else "adult"


def load_passages(directory: Path = KNOWLEDGE_DIR) -> List[Passage]:
    """Read every markdown file in the knowledge directory into passages."""
    passages: List[Passage] = []
    for path in sorted(Path(directory).glob("*.md")):
        species = None
        heading = None
        body: List[str] = []

        def flush() -> None:
            if heading and body:
                passages.append(
                    Passage(
                        source=f"{path.name}#{heading}",
                        heading=heading,
                        text=" ".join(body).strip(),
                        species=species,
                    )
                )

        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("species:"):
                species = line.split(":", 1)[1].strip().lower() or None
            elif line.startswith("## "):
                flush()
                heading, body = line[3:].strip(), []
            elif line.startswith("# "):
                continue
            elif line.strip():
                body.append(line.strip())
        flush()
    logger.info("Loaded %d passages from %s", len(passages), directory)
    return passages


STAGE_WORDS = {
    "young": {"puppy", "kitten"},
    "senior": {"senior"},
    "adult": {"adult"},
}


def retrieve(
    query: str,
    species: str,
    age: int = 3,
    top_k: int = 3,
    passages: Optional[List[Passage]] = None,
) -> List[Passage]:
    """Return the top_k passages for a query, best first.

    Passages with a score of zero are dropped, so an empty list means the
    knowledge base has nothing relevant (the planner treats that as a signal
    to fall back instead of guessing).
    """
    passages = passages if passages is not None else load_passages()
    species = species.strip().lower()
    candidates = [p for p in passages if p.species in (None, species)]
    if not candidates:
        return []

    docs = [_tokens(p.heading + " " + p.text) for p in candidates]
    n = len(docs)
    df: dict = {}
    for words in docs:
        for w in set(words):
            df[w] = df.get(w, 0) + 1

    stage = life_stage(species, age)
    query_words = set(_tokens(query)) - {species}

    scored: List[Passage] = []
    for p, words in zip(candidates, docs):
        if not words:
            continue
        counts = {w: words.count(w) for w in set(words)}
        score = 0.0
        for w in query_words:
            if w in counts:
                idf = math.log((n + 1) / (df[w] + 0.5)) + 1
                score += (counts[w] / len(words)) * idf
        # Life-stage fit (only for passages that already matched the query):
        # boost a heading that names the pet's stage, demote one naming another.
        heading_words = set(_tokens(p.heading))
        if score > 0:
            if STAGE_WORDS[stage] & heading_words:
                score *= 2.0
            elif any(STAGE_WORDS[o] & heading_words for o in STAGE_WORDS if o != stage):
                score *= 0.4
        # Heading matches are a strong signal.
        score += 0.05 * len(query_words & heading_words)
        if score > 0:
            scored.append(Passage(p.source, p.heading, p.text, p.species, round(score, 4)))

    scored.sort(key=lambda p: p.score, reverse=True)
    top = scored[:top_k]
    logger.info(
        "Retrieved %d passage(s) for query=%r species=%s stage=%s: %s",
        len(top), query, species, stage, [(p.source, p.score) for p in top],
    )
    return top
