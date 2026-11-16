# Model Card: PawPal+ AI

## Overview

- **System:** PawPal+ AI, a retrieval-augmented pet-care planner built on the Module 2 PawPal+ scheduler.
- **Model:** Google Gemini (`gemini-3.5-flash-lite` by default, set in `ai_planner.py`), called through the Gemini API.
- **Task:** Given a pet's species, age and focus area, suggest care tasks (title, time, duration, priority, frequency) grounded in passages retrieved from a local knowledge base (`knowledge/*.md`).
- **Intended use:** Helping a pet owner draft a daily care plan. The owner reviews every suggestion before it is added.
- **Not intended for:** Medical advice, medication dosing, diagnosing illness or emergencies. The system refuses dose questions and tells the user to contact a vet.

## How the system limits the model

- **Grounding:** the prompt contains only the pet profile and the retrieved passages. Each suggestion must cite one of them, and the validator rejects citations that were not retrieved.
- **Validation:** suggestions need a valid priority, a positive duration and a valid time.
- **Safety rules:** a regex filter blocks medication doses in the user's request and in model output.
- **Fallback:** no API key, an API error, empty retrieval or invalid output all route to the original rule-based scheduler.
- **Human review:** nothing reaches the schedule until the owner accepts it.
- **Logging:** retrieval hits, API calls, validation failures and fallbacks are written to `pawpal.log`.

## Evaluation results

| Check | Result |
|-------|--------|
| Unit tests (`pytest`) | 35/35 pass |
| Offline scenarios (`eval.py`) | 17/17 pass (9 retrieval, 3 guardrail, 5 fallback); per-scenario table in README |
| Live Gemini scenarios (`eval.py --live`) | 9/9 pass |
| Live average confidence | 0.98 (range 0.89 to 1.0), 0 suggestions rejected |

The live pass criteria are mechanical: at least one suggestion, every citation is a retrieved passage, no doses. They do not measure whether the advice is *good*. That needs a vet or an experienced owner to judge, and I have not had the output reviewed by one.

## Collaboration with AI

I used Claude as a coding and design partner across the project: drafting the UML, turning it into class skeletons, filling in method bodies in small steps, and later building the retriever, planner, guardrails and evaluation harness. Gemini is the model inside the product. The most useful pattern was small, specific prompts tied to my own design, because I could check the output against my UML and my tests. Open-ended prompts gave plausible code that was harder to verify.

**A suggestion I accepted (after checking it).** The AI suggested adding a `frequency` field to `Task`. It was not in my original UML. I checked it against the design and agreed it was needed, because one task can repeat daily or weekly and recurrence depends on it. I accepted it deliberately and recorded the design change in `reflection.md`. It later became the basis for recurring tasks and for the `frequency` field the AI planner returns.

**A suggestion I revised.** The AI's first `generate_schedule()` sorted tasks by priority as a string. That orders "high", "low", "medium", which puts low priority ahead of medium. It looked correct and I only caught it by reading the printed schedule. I replaced it with a `PRIORITY_ORDER` lookup (high, medium, low mapped to 0, 1, 2), made it case-insensitive and ranked unknown values last instead of raising an error. I then added tests so the behavior is checked by code.

## Limitations and biases

- **Small, hand-written knowledge base.** The guidance is only as good as the markdown files I wrote. It covers a limited set of species and topics and is not reviewed by a veterinarian. Anything not in it gets no suggestions, which is intended, but it means the system can feel unhelpful for less common pets.
- **Keyword retrieval.** TF-IDF matching misses paraphrases ("stroll" for "walk") and favors short passages, so a general passage such as "Walk timing" can outrank a species-specific one. The right passage was always in the top 3 in my tests, but not always first.
- **Biased toward the species and life stages I covered.** Dogs and cats get far better coverage than other animals. Breed, weight and health conditions are not considered, so advice for an 11-year-old Shiba Inu is the same as for any senior dog.
- **Safety filter is a regex.** It catches common dose phrasing ("5 mg", "half a tablet") but not every possible wording, and it can miss indirect requests. It is a safety net, not a guarantee.
- **Confidence score is weakly informative.** In live runs it was nearly always close to 1.0, because the model rarely broke the rules and retrieval scores were high. A high score means the output was well-formed and grounded, not that the advice is correct.
- **Model can still be wrong or inconsistent.** Even with grounding, Gemini may phrase things overconfidently or choose times that don't suit a particular household. The citation check proves the source was retrieved, not that the model represented it accurately.
- **Evaluation is narrow.** 26 scenarios written by me, with mechanical pass criteria. They cannot catch subtle quality problems.
- **Scheduler gaps remain.** Conflict detection compares start times only, not overlapping durations, and the app does not save data between sessions.
- **Privacy.** Pet details and the request text are sent to the Gemini API. The API key lives in `.env`, which is kept out of version control.

## Misuse and mitigations

**Could it be misused?** Yes. The main risk is someone treating the output as veterinary advice, especially for medication or a sick animal. A second risk is a user phrasing a dose request indirectly to get past the filter. Mitigations are the dose-blocking filter, the refusal message pointing to a vet, the knowledge base excluding medication dosing, and the human review step. A real deployment would also need a visible disclaimer, a vet-reviewed knowledge base and monitoring of real user requests.

## What surprised me while testing reliability

- **Retrieval, not the prompt, was the weak point.** An 11-year-old dog's senior passage lost to the puppy passage, so the suggestions would have been worse. Most of my debugging went into life-stage weighting and query terms rather than prompt wording. When the right passage was in the prompt, Gemini used it: it suggested three 20-minute walks and explained that older dogs do better with shorter outings.
- **Confidence barely moved on real output.** I expected the score to vary across live runs. It averaged 0.98 (range 0.89 to 1.0) because the model rarely broke the rules. It only dropped meaningfully (0.62) on my hand-built partly invalid batch. A high score tells me the output was well-formed, not that it was good.
- **The model itself was the unreliable part.** My first choice (`gemini-2.5-flash`) was no longer available to new users, and `gemini-3.8-flash` timed out under load. The app showed only a generic "AI step failed" message. I found the cause in `pawpal.log`, then switched to a faster default model, added a 30 s timeout and added retries on temporary errors. The lesson was that failures need enough logged detail to diagnose, and that the app must degrade to the rule-based scheduler instead of hanging.
- **Empty input needed explicit tests.** I added empty and whitespace-only requests to `eval.py` so graceful handling is checked rather than assumed.

## What I would do next

- Have a vet or experienced owner rate sample suggestions, and use those ratings to calibrate the confidence score.
- Replace TF-IDF with embeddings, or combine both, and measure the change on the same scenarios.
- Expand the knowledge base with sources I can cite, and add breed, weight and health inputs.
- Add real overlap detection and persistence to the scheduler.
