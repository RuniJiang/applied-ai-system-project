import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task(title="Walk", duration=30, priority="high", time="08:00")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_complete_recurring_task_creates_next_occurrence():
    pet = Pet(name="Mochi", species="dog")
    owner = Owner(name="Runi")
    scheduler = Scheduler(owner)
    daily = Task("Walk", 30, "high", "08:00", "daily", due_date=date(2026, 1, 1))
    weekly = Task("Bath", 20, "low", "10:00", "weekly", due_date=date(2026, 1, 1))
    once = Task("Vet", 15, "high", "11:00", "once", due_date=date(2026, 1, 1))
    for t in (daily, weekly, once):
        scheduler.add_task(pet, t)

    next_daily = scheduler.complete_task(pet, daily)
    next_weekly = scheduler.complete_task(pet, weekly)
    next_once = scheduler.complete_task(pet, once)

    assert daily.completed and not next_daily.completed
    assert next_daily.due_date == date(2026, 1, 2)
    assert next_weekly.due_date == date(2026, 1, 8)
    assert next_once is None
    assert len(pet.tasks) == 5


def test_sort_by_time_returns_chronological_order():
    # "9:00" vs "10:00" would misorder under plain string sorting
    tasks = [
        Task("Dinner", 20, "medium", "18:30"),
        Task("Lunch", 20, "medium", "10:00"),
        Task("Breakfast", 20, "medium", "9:00"),
        Task("Walk", 30, "high", "07:15"),
    ]

    result = Scheduler.sort_by_time(tasks)

    assert [t.title for t in result] == ["Walk", "Breakfast", "Lunch", "Dinner"]
    assert [t.title for t in tasks][0] == "Dinner"  # input not mutated


def test_marking_daily_task_complete_creates_task_for_next_day():
    pet = Pet(name="Mochi", species="dog")
    scheduler = Scheduler(Owner(name="Runi"))
    daily = Task("Walk", 30, "high", "08:00", "daily", due_date=date(2026, 1, 31))
    scheduler.add_task(pet, daily)

    next_task = scheduler.complete_task(pet, daily)

    assert daily.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == date(2026, 2, 1)  # rolls over month boundary
    assert next_task.title == daily.title and next_task.time == daily.time
    assert next_task in pet.tasks
    assert len(pet.tasks) == 2


def test_detect_conflicts_flags_duplicate_times():
    owner = Owner(name="Runi")
    scheduler = Scheduler(owner)
    mochi = Pet(name="Mochi", species="dog")
    whiskers = Pet(name="Whiskers", species="cat")
    day = date(2026, 1, 1)
    scheduler.add_task(mochi, Task("Walk", 30, "high", "08:00", due_date=day))
    scheduler.add_task(whiskers, Task("Feed", 10, "high", "8:00", due_date=day))
    scheduler.add_task(mochi, Task("Brush", 10, "low", "09:00", due_date=day))

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "Walk" in warnings[0] and "Feed" in warnings[0]
    assert "different pets" in warnings[0]


def test_detect_conflicts_ignores_non_conflicts():
    scheduler = Scheduler(Owner(name="Runi"))
    pet = Pet(name="Mochi", species="dog")
    scheduler.add_task(pet, Task("Walk", 30, "high", "08:00", due_date=date(2026, 1, 1)))
    scheduler.add_task(pet, Task("Feed", 10, "high", "08:00", due_date=date(2026, 1, 2)))
    done = Task("Brush", 10, "low", "08:00", due_date=date(2026, 1, 1))
    done.completed = True
    scheduler.add_task(pet, done)

    assert scheduler.detect_conflicts() == []


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feed", duration=10, priority="medium", time="09:00"))

    assert len(pet.tasks) == 1
