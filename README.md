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

All of these features live in [pawpal_system.py](pawpal_system.py).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting | `Scheduler.sort_by_time()` (also `generate_schedule()`) | Orders tasks by time of day |
| Filtering | `Scheduler.filter_tasks()` | By completion status and/or pet name |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns when pending tasks share a start time |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.complete_task()` | Daily and weekly tasks respawn when completed |

### Sorting

`Scheduler.sort_by_time(tasks)` is a static method that returns a new list ordered earliest to latest. It sorts on minutes since midnight (via the `_time_to_minutes()` helper) instead of the raw string, so `"9:00"` correctly comes before `"10:00"`. The sort is stable, so tasks with the same time keep their input order, and the input list is not modified. An invalid time raises `ValueError`.

`Scheduler.generate_schedule()` builds the daily plan from pending tasks due today or earlier. It sorts them by time first and then by priority (high → medium → low) to break ties.

### Filtering

`Scheduler.filter_tasks(completed=None, pet_name=None)` narrows the owner's tasks:

- `completed=True` returns finished tasks and `completed=False` returns pending ones.
- `pet_name="Mochi"` returns only that pet's tasks. The match is case-insensitive and ignores surrounding whitespace.
- A filter left as `None` is not applied, so calling it with no arguments returns every task.
- Both filters can be combined, and a task must match both.

### Conflict detection

`Scheduler.detect_conflicts()` is a lightweight check that returns a list of warning strings instead of raising errors or blocking the schedule. It groups pending tasks by (due date, start time). Any group with two or more tasks produces one warning that lists the tasks and says whether they belong to the same pet or to different pets. Completed tasks are ignored, and tasks with an unparseable time are skipped. Only identical start times are flagged, because durations are not compared, so partially overlapping tasks are not detected.

### Recurring tasks

Each `Task` has a `frequency` (`"once"`, `"daily"` or `"weekly"`) and a `due_date`. `Task.mark_complete()` sets `completed = True`. If the frequency is recurring, it returns a copy of the task with `completed = False` and the due date moved forward by 1 day (daily) or 7 days (weekly). One-off tasks return `None`.

`Scheduler.complete_task(pet, task)` calls `mark_complete()` and adds the new occurrence to the same pet. The completed original stays in the list as a record, and `generate_schedule()` only shows the new occurrence once its due date arrives.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
