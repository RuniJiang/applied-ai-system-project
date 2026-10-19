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


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feed", duration=10, priority="medium", time="09:00"))

    assert len(pet.tasks) == 1
