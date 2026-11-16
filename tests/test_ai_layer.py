"""Tests for the retriever, validator, guardrails and planner (no network)."""

import json

import pytest

from ai_planner import (
    VET_MESSAGE,
    check_request_safety,
    compute_confidence,
    parse_response,
    suggest_tasks,
    validate_suggestion,
)
from pawpal_system import Pet, Task
from retriever import life_stage, retrieve

SRC = "dog_exercise.md#Senior dog exercise"


def good(**over):
    item = {
        "title": "Gentle walk", "duration": 20, "priority": "medium", "time": "08:00",
        "frequency": "daily", "reason": "Seniors need shorter walks.", "source": SRC,
    }
    item.update(over)
    return item


# Retriever ---------------------------------------------------------------------
def test_life_stage_thresholds():
    assert life_stage("dog", 0) == "young"
    assert life_stage("dog", 8) == "senior"
    assert life_stage("cat", 8) == "adult"
    assert life_stage("cat", 10) == "senior"


def test_senior_dog_gets_senior_passage_over_puppy():
    sources = [p.source for p in retrieve("exercise", "dog", age=11)]
    assert sources.index(SRC) < sources.index("dog_exercise.md#Puppy exercise")


def test_species_filter_excludes_other_species():
    assert all(p.species in (None, "cat") for p in retrieve("feeding meals", "cat", age=4))


def test_irrelevant_query_returns_nothing():
    assert retrieve("swimming lessons", "cat", age=4) == []


# Validator / guardrails ------------------------------------------------------------
def test_valid_suggestion_passes():
    assert validate_suggestion(good(), {SRC}).title == "Gentle walk"


@pytest.mark.parametrize(
    "bad",
    [
        {"duration": 0}, {"duration": 999}, {"duration": "abc"},
        {"priority": "urgent"}, {"time": "25:99"}, {"frequency": "hourly"},
        {"title": ""}, {"reason": ""}, {"source": "made_up.md#Nope"},
        {"reason": "Give 5 mg every morning."}, {"title": "Give half a tablet"},
    ],
)
def test_invalid_suggestions_rejected(bad):
    with pytest.raises(ValueError):
        validate_suggestion(good(**bad), {SRC})


def test_dose_request_is_blocked():
    assert check_request_safety("how much ibuprofen can I give my dog") == VET_MESSAGE
    assert check_request_safety("what dosage of pills") == VET_MESSAGE
    assert check_request_safety("daily exercise") is None


def test_parse_response_handles_code_fence():
    assert parse_response("```json\n[{\"a\": 1}]\n```") == [{"a": 1}]
    with pytest.raises(ValueError):
        parse_response("sorry, no JSON")


def test_confidence_bounds():
    assert compute_confidence([], 0, 0) == 0.0


# Planner ------------------------------------------------------------------------------
SENIOR = Pet("Mochi", "dog", "Shiba Inu", 11)


def test_planner_uses_retrieved_source_and_scores_confidence():
    result = suggest_tasks(SENIOR, "exercise walk", llm=lambda p: json.dumps([good()]))
    assert not result.fallback and len(result.suggestions) == 1
    assert result.suggestions[0].source == SRC
    assert 0 < result.confidence <= 1


def test_prompt_contains_retrieved_text():
    seen = {}

    def fake(prompt):
        seen["p"] = prompt
        return "[]"

    suggest_tasks(SENIOR, "exercise walk", llm=fake)
    assert "shorter, gentler walks" in seen["p"]  # text from the senior passage


def test_unsafe_focus_never_calls_llm():
    def boom(prompt):
        raise AssertionError("LLM must not be called")

    result = suggest_tasks(SENIOR, "ibuprofen dose", llm=boom)
    assert result.blocked and result.message == VET_MESSAGE


def test_llm_error_falls_back():
    def broken(prompt):
        raise RuntimeError("network down")

    result = suggest_tasks(SENIOR, "exercise walk", llm=broken)
    assert result.fallback and not result.suggestions


def test_garbage_reply_falls_back():
    assert suggest_tasks(SENIOR, "exercise walk", llm=lambda p: "I like dogs").fallback


def test_no_passages_falls_back():
    cat = Pet("Luna", "cat", age=4)
    assert suggest_tasks(cat, "swimming lessons", llm=lambda p: "[]").fallback


def test_missing_api_key_falls_back(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    result = suggest_tasks(SENIOR, "exercise walk")
    assert result.fallback and "API key" in result.message


def test_mixed_batch_keeps_valid_drops_invalid():
    reply = json.dumps([good(), good(title="Bad", duration=-5), good(title="Dose", reason="2 mg daily")])
    result = suggest_tasks(SENIOR, "exercise walk", llm=lambda p: reply)
    assert [s.title for s in result.suggestions] == ["Gentle walk"]
    assert len(result.rejected) == 2
    assert result.confidence < 1.0


def test_duplicates_and_time_conflicts_dropped():
    existing = [Task("Gentle walk", 20, "high", "09:00")]
    reply = json.dumps([good(), good(title="Play", time="09:00"), good(title="Brush", time="10:00")])
    result = suggest_tasks(SENIOR, "exercise walk", existing=existing, llm=lambda p: reply)
    assert [s.title for s in result.suggestions] == ["Brush"]
