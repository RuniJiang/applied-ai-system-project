# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

The logic layer lives in [pawpal_system.py](pawpal_system.py) and is built from four classes:

- **Task** (dataclass): one care activity with a title, duration, priority, time, frequency, and completion flag. `mark_complete()` marks it done.
- **Pet** (dataclass): a pet's profile plus its own list of `Task`s, managed with `add_task()` and `remove_task()`.
- **Owner** (dataclass): holds a list of `Pet`s. `add_pet()` registers a pet, and `get_all_tasks()` flattens every pet's tasks into one list.
- **Scheduler**: wraps an `Owner`. `add_task(pet, task)` attaches a task to a pet (registering the pet if it is new). `generate_schedule()` collects all pending tasks from the owner and sorts them by time, then priority (high → low). `display_schedule()` prints the result with each task's pet name.

How they fit together: `Owner` → has many `Pet`s → each has many `Task`s. The `Scheduler` sits on top of that hierarchy, reads tasks through the `Owner`, and produces the ordered daily plan. [main.py](main.py) is a demo script that builds sample data and prints the schedule.

## 🖥️ Sample Output

Output from running `python3 main.py`, which builds an owner with two pets and four tasks and prints the generated schedule:

```
Today's schedule for Runi:
  07:30  Morning walk (Mochi) - 30 min, high priority, daily
  08:00  Breakfast (Luna) - 10 min, high priority, daily
  12:00  Flea medication (Mochi) - 5 min, medium priority, weekly
  18:00  Play session (Luna) - 20 min, low priority, daily
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
