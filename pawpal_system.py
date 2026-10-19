"""PawPal+ logic layer: classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import List, Optional

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
RECURRENCE_DELTAS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def _time_to_minutes(time_str: str) -> int:
    """Convert an "HH:MM" string (e.g. "8:30" or "08:30") to minutes since midnight."""
    parsed = datetime.strptime(time_str.strip(), "%H:%M")
    return parsed.hour * 60 + parsed.minute


@dataclass
class Task:
    title: str  # description of the activity
    duration: int  # minutes
    priority: str  # e.g. "low", "medium", "high"
    time: str  # e.g. "08:00"
    frequency: str = "once"  # e.g. "once", "daily", "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as completed.

        For "daily" or "weekly" tasks, returns a new pending Task for the next
        occurrence (due_date + 1 day or + 7 days); otherwise returns None.
        """
        self.completed = True
        delta = RECURRENCE_DELTAS.get(self.frequency.lower())
        if delta is None:
            return None
        return replace(self, completed=False, due_date=self.due_date + delta)


@dataclass
class Pet:
    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet if present."""
        if task in self.tasks:
            self.tasks.remove(task)


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that manages tasks for the given owner."""
        self.owner = owner

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a task to the given pet (adding the pet to the owner if new)."""
        if pet not in self.owner.pets:
            self.owner.add_pet(pet)
        pet.add_task(task)

    def complete_task(self, pet: Pet, task: Task) -> Optional[Task]:
        """Mark a pet's task complete and schedule its next occurrence if recurring.

        Returns the newly created task, or None for one-off tasks.
        """
        next_task = task.mark_complete()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def filter_tasks(
        self, completed: Optional[bool] = None, pet_name: Optional[str] = None
    ) -> List[Task]:
        """Return tasks filtered by completion status and/or pet name (case-insensitive).

        A filter left as None is not applied, so no arguments returns all tasks.
        """
        pets = self.owner.pets
        if pet_name is not None:
            pets = [p for p in pets if p.name.lower() == pet_name.strip().lower()]
        return [
            t
            for pet in pets
            for t in pet.tasks
            if completed is None or t.completed == completed
        ]

    @staticmethod
    def sort_by_time(tasks: List[Task]) -> List[Task]:
        """Return tasks sorted chronologically by their "HH:MM" time (earliest first)."""
        return sorted(tasks, key=lambda t: _time_to_minutes(t.time))

    def generate_schedule(self) -> List[Task]:
        """Return the owner's pending tasks due today or earlier, ordered by time then priority."""
        today = date.today()
        pending = [
            t
            for t in self.owner.get_all_tasks()
            if not t.completed and t.due_date <= today
        ]
        return sorted(
            pending,
            key=lambda t: (
                _time_to_minutes(t.time),
                PRIORITY_ORDER.get(t.priority.lower(), len(PRIORITY_ORDER)),
            ),
        )

    def display_schedule(self) -> None:
        """Print the generated schedule."""
        owner_of = {id(t): pet.name for pet in self.owner.pets for t in pet.tasks}
        schedule = self.generate_schedule()
        print(f"Today's schedule for {self.owner.name}:")
        if not schedule:
            print("  (no pending tasks)")
        for task in schedule:
            print(
                f"  {task.time}  {task.title} ({owner_of[id(task)]}) - "
                f"{task.duration} min, {task.priority} priority, {task.frequency}"
            )
