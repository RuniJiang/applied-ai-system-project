"""Evaluation harness for the PawPal+ AI layer.

    python eval.py          offline: retrieval quality + guardrails + fallbacks
    python eval.py --live   also runs each retrieval scenario through the real
                            Gemini API (needs GEMINI_API_KEY) and checks the
                            output end to end

Exit code is 0 only if every scenario passes.
"""

import json
import os
import sys

from ai_planner import DOSE_PATTERN, VET_MESSAGE, api_key, configure_logging, suggest_tasks
from pawpal_system import Pet
from retriever import retrieve

GOOD = {
    "title": "Walk", "duration": 20, "priority": "medium", "time": "08:00",
    "frequency": "daily", "reason": "Fits the guidance.", "source": "",
}

# (label, species, age, focus, passage that must appear in the top 3)
RETRIEVAL = [
    ("senior dog exercise", "dog", 11, "exercise walk", "dog_exercise.md#Senior dog exercise"),
    ("puppy exercise", "dog", 0, "exercise walk", "dog_exercise.md#Puppy exercise"),
    ("adult dog feeding", "dog", 4, "feeding meals schedule", "dog_feeding.md#Adult dog feeding schedule"),
    ("kitten feeding", "cat", 0, "feeding meals", "cat_care.md#Kitten feeding"),
    ("cat play", "cat", 4, "play enrichment toys", "cat_care.md#Cat play and enrichment"),
    ("cat litter", "cat", 6, "litter box scoop", "cat_care.md#Litter box care"),
    ("dog grooming", "dog", 3, "brushing grooming coat", "grooming.md#Brushing frequency"),
    ("nail trimming", "cat", 5, "nail trim", "grooming.md#Nail trimming"),
    ("preventive meds", "dog", 5, "flea heartworm preventive reminder", "medication_safety.md#Preventive care schedule"),
]

results = []  # (name, input, criteria, passed, detail)


def record(name: str, inp: str, criteria: str, passed: bool, detail: str = "") -> None:
    results.append((name, inp, criteria, passed, detail))
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))


def offline() -> None:
    print("\nRetrieval quality (expected passage in top 3)")
    for label, species, age, focus, expected in RETRIEVAL:
        got = [p.source for p in retrieve(focus, species, age, top_k=3)]
        record(f"retrieval: {label}", f"{species}, age {age}, \"{focus}\"",
               f"{expected} in top 3", expected in got, f"top={got[:1]}")

    print("\nGuardrails")
    pet = Pet("Rex", "dog", age=11)
    record("dose request blocked, LLM never called", "\"how much ibuprofen to give\"",
           "returns vet message; LLM not called", suggest_tasks(
               pet, "how much ibuprofen to give", llm=lambda p: 1 / 0).message == VET_MESSAGE)

    src = retrieve("exercise walk", "dog", 11)[0].source
    bad_batch = json.dumps([
        {**GOOD, "source": src},
        {**GOOD, "title": "Dose", "reason": "Give 10 mg daily.", "source": src, "time": "09:00"},
        {**GOOD, "title": "Fake cite", "source": "nope.md#X", "time": "10:00"},
        {**GOOD, "title": "Bad time", "time": "99:99", "source": src},
    ])
    r = suggest_tasks(pet, "exercise walk", llm=lambda p: bad_batch)
    record("invalid items dropped, valid kept", "4 items: 1 valid, dose, fake citation, bad time",
           "1 kept, 3 rejected", len(r.suggestions) == 1 and len(r.rejected) == 3,
           f"kept={len(r.suggestions)} rejected={len(r.rejected)}")
    record("confidence drops when output is partly invalid", "same partly invalid batch",
           "confidence < 0.9", r.confidence < 0.9, f"confidence={r.confidence}")

    print("\nFallbacks")
    record("no relevant guidance -> fallback", "cat, \"swimming lessons\"", "fallback=True", suggest_tasks(
        Pet("Luna", "cat", age=4), "swimming lessons", llm=lambda p: "[]").fallback)
    record("LLM exception -> fallback", "LLM raises ZeroDivisionError", "fallback=True", suggest_tasks(pet, "exercise walk", llm=lambda p: 1 / 0).fallback)
    for label, focus in (("empty input", ""), ("whitespace-only input", "   ")):
        try:
            r = suggest_tasks(pet, focus, llm=lambda p: "[]")
            record(f"{label} handled gracefully", repr(focus), "no crash; fallback=True", r.fallback)
        except Exception as exc:
            record(f"{label} handled gracefully", repr(focus), "no crash; fallback=True", False,
                   f"crashed: {type(exc).__name__}")
    record("non-JSON reply -> fallback", "LLM replies \"hello\"", "fallback=True", suggest_tasks(pet, "exercise walk", llm=lambda p: "hello").fallback)


def live() -> None:
    print("\nLive end-to-end (real Gemini API)")
    if not api_key():
        print("  GEMINI_API_KEY not set; skipping live scenarios.")
        return
    confidences = []
    for label, species, age, focus, expected in RETRIEVAL:
        r = suggest_tasks(Pet("Test", species, age=age), focus)
        retrieved = {p.source for p in r.passages}
        ok = (
            not r.fallback
            and len(r.suggestions) >= 1
            and all(s.source in retrieved for s in r.suggestions)
            and not any(DOSE_PATTERN.search(s.title + s.reason) for s in r.suggestions)
        )
        if not r.fallback:
            confidences.append(r.confidence)
        record(f"live: {label}", f"{species}, age {age}, \"{focus}\"",
               "no fallback; >=1 suggestion; citations retrieved; no doses", ok,
               f"suggestions={len(r.suggestions)} rejected={len(r.rejected)} confidence={r.confidence}")
    if confidences:
        print(f"  average confidence over live runs: {sum(confidences) / len(confidences):.2f}")


if __name__ == "__main__":
    configure_logging()
    offline()
    if "--live" in sys.argv:
        live()
    print("\nResults table (markdown)\n")
    print("| Test | Input | Evaluation criteria | Result |")
    print("|------|-------|---------------------|--------|")
    for name, inp, criteria, ok, detail in results:
        res = "Pass" if ok else "Fail" + (f" ({detail})" if detail else "")
        print(f"| {name} | {inp} | {criteria} | {res} |".replace("\\", ""))
    passed = sum(1 for *_, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} scenarios passed")
    sys.exit(0 if passed == len(results) else 1)
