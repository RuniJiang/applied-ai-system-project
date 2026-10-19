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

Run the full test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

- **Task completion:** marking a task complete flips its status.
- **Recurrence logic:** completing a daily task creates a pending copy due the next day (including across month boundaries); weekly tasks advance 7 days; one-off tasks create nothing.
- **Sorting correctness:** tasks come back in chronological order by real time (so `9:00` sorts before `10:00`), without mutating the input.
- **Conflict detection:** pending tasks sharing a date and start time are flagged (across pets too, and `8:00` matches `08:00`); completed tasks and different dates are not.
- **Pet task management:** adding a task increases the pet's task count.

### Sample test output

```
============================= test session starts ==============================
platform darwin -- Python 3.13.15, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/runijiang/Documents/GitHub/ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 7 items

tests/test_pawpal.py .......                                             [100%]

============================== 7 passed in 0.01s ===============================
```

### Confidence Level: ⭐⭐⭐⭐ (4/5)

All 7 tests pass and cover the core behaviors: sorting, recurrence, and conflict detection. I stop short of 5 stars because some paths are untested: filtering, `generate_schedule`, invalid time strings (one bad time raises in sorting and scheduling), duplicate recurrences from completing the same task twice, and overlapping durations (conflicts only compare start times).

## ✨ Features

- **Sorting by time:** `Scheduler.sort_by_time()` converts each `"HH:MM"` string to minutes since midnight before sorting, so `"9:00"` comes before `"10:00"`. The sort is stable and returns a new list without changing the original. An unparseable time raises `ValueError`.
- **Priority-aware daily schedule:** `generate_schedule()` keeps pending tasks due today or earlier. It sorts them by time and uses priority (high → medium → low) as the tiebreaker. Unknown priority values sort last.
- **Filtering by pet and status:** `filter_tasks()` filters by completion status, by pet name, or by both together (AND). Pet name matching ignores case and surrounding whitespace. A filter left as `None` isn't applied.
- **Conflict warnings:** `detect_conflicts()` groups pending tasks by (due date, start time) in a single pass and warns about every group with two or more tasks. It works across pets and within a single pet, and the message says "same pet" or "different pets". Tasks with an invalid time are skipped instead of crashing the check. It compares start times only, so overlapping durations aren't detected.
- **Daily and weekly recurrence:** `Task.mark_complete()` marks the task done. For `daily` or `weekly` tasks it also returns a copy with `completed=False` and the due date moved forward by 1 or 7 days. `Scheduler.complete_task()` attaches that copy to the same pet. The completed original stays in the list as history. One-off tasks return `None`.
- **Streamlit UI integration:** Conflicts appear as warning banners above the task list. The task table can be filtered and sorted, and completing a recurring task shows a confirmation that the next one was scheduled.

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

### Main UI features

Run `streamlit run app.py` to open the app. From top to bottom, a user can:

- **Set the owner name** in the Owner field.
- **Add pets** by entering a name and choosing a species (dog, cat or other). Empty names and duplicate names (case-insensitive) are rejected with a message. A table lists each pet and its task count.
- **Schedule tasks** by picking a pet, then entering a title, duration (1-240 minutes), priority, time and frequency (once, daily or weekly).
- **Review the Task Overview**, which shows Pending, Completed and Conflicts counts, plus a warning banner for each scheduling conflict.
- **Browse all tasks** in a table that can be filtered by pet and by status (All, Pending, Completed) and is always sorted by time.
- **Mark a task complete.** If the task is daily or weekly, the app confirms the date of the next occurrence it created.
- **Generate a schedule** for today with the Generate schedule button.

### Example workflow

1. **Add a pet.** Type "Mochi", choose "dog" and click **Add pet**. Mochi appears in the pets table with 0 tasks.
2. **Schedule a task.** Select Mochi, enter "Evening walk", 30 minutes, medium priority, 17:00, daily, then click **Add task**.
3. **Add a second task at the same time.** Add "Grooming" for another pet at 17:00. The Conflicts metric changes to 1 and a warning names both tasks.
4. **Filter and sort.** In All Tasks, choose Mochi and Pending to see only her open tasks, ordered by time.
5. **Complete a recurring task.** Select "Evening walk" and click **Mark complete**. The app confirms the next occurrence is scheduled for tomorrow.
6. **View today's schedule.** Click **Generate schedule** to see pending tasks due today or earlier, ordered by time and then priority. The new occurrence does not appear until its due date.

### Scheduler behaviors shown

- **Sorting by time:** "9:00" is placed before "10:00" because times are compared as minutes since midnight, and ties keep their input order.
- **Priority tiebreaking:** The generated schedule orders same-time tasks high, then medium, then low.
- **Filtering:** Pet and status filters combine, and pet names match case-insensitively. An unknown pet returns no tasks.
- **Conflict warnings:** Pending tasks sharing a date and start time are reported once per group, labeled "same pet" or "different pets". Completed tasks are ignored.
- **Recurrence:** Completing a daily or weekly task keeps the original as history and adds a copy due 1 or 7 days later.

### Sample CLI output

`python main.py` exercises the same logic without the UI:

```text

Insertion order (unsorted):
  18:00  Play session - low, pending
  10:00  Vet call - high, pending
   9:00  Breakfast - high, done
   9:00  Breakfast - high, pending
  12:00  Flea medication - medium, pending
  07:30  Morning walk - high, done
  17:00  Evening walk - medium, pending
  07:30  Morning walk - high, pending

All tasks sorted by time:
  07:30  Morning walk - high, done
  07:30  Morning walk - high, pending
   9:00  Breakfast - high, done
   9:00  Breakfast - high, pending
  10:00  Vet call - high, pending
  12:00  Flea medication - medium, pending
  17:00  Evening walk - medium, pending
  18:00  Play session - low, pending

Pending only, sorted:
  07:30  Morning walk - high, pending
   9:00  Breakfast - high, pending
  10:00  Vet call - high, pending
  12:00  Flea medication - medium, pending
  17:00  Evening walk - medium, pending
  18:00  Play session - low, pending

Completed only:
  07:30  Morning walk - high, done
   9:00  Breakfast - high, done

Mochi's tasks, sorted:
  07:30  Morning walk - high, done
  07:30  Morning walk - high, pending
  12:00  Flea medication - medium, pending
  17:00  Evening walk - medium, pending

Luna's pending tasks, sorted:
   9:00  Breakfast - high, pending
  10:00  Vet call - high, pending
  18:00  Play session - low, pending

Unknown pet:
  (none)

Today's schedule for Runi:
  10:00  Vet call (Luna) - 15 min, high priority, once
  12:00  Flea medication (Mochi) - 5 min, medium priority, weekly
  17:00  Evening walk (Mochi) - 30 min, medium priority, daily
  18:00  Play session (Luna) - 20 min, low priority, daily

Conflict check (no conflicts expected):
  (none)

Conflict check after adding overlapping tasks:
  WARNING: 2 tasks at 17:00 on 2026-10-18 (different pets): 'Grooming' (Luna), 'Evening walk' (Mochi)
  WARNING: 2 tasks at 18:00 on 2026-10-18 (same pet): 'Play session' (Luna), 'Medication' (Luna)
```
