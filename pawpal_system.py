"""PawPal+ logic layer: classes for owners, pets, tasks, and scheduling."""

from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import List, Optional

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
RECURRENCE_DELTAS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def _time_to_minutes(time_str: str) -> int:
    """Convert an "HH:MM" string (e.g. "8:30" or "08:30") to minutes since midnight.

    Used as the numeric sort/grouping key for task times, since comparing raw
    strings would misorder values like "9:00" and "10:00".

    Args:
        time_str: 24-hour time; surrounding whitespace is ignored.

    Returns:
        Minutes since midnight (0-1439).

    Raises:
        ValueError: If the string is not a valid "HH:MM" time.
    """
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

        Recurrence algorithm: look up frequency (case-insensitive) in
        RECURRENCE_DELTAS; if found, copy this task with completed=False and
        due_date advanced by that delta. The original is left as a completed
        record, so history is preserved.

        Returns:
            A new pending Task for the next occurrence ("daily" = +1 day,
            "weekly" = +7 days), or None for non-recurring tasks.
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
    weight_kg: float = 0.0  # 0 means unknown
    notes: str = ""  # optional health or behaviour notes, e.g. "stiff hips"

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

        Delegates to Task.mark_complete() and, when it yields a next
        occurrence, attaches that task to the same pet.

        Args:
            pet: The pet that owns the task.
            task: The task to complete.

        Returns:
            The newly created task, or None for one-off tasks.
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
        Filters combine with AND. Pets are narrowed first by name, then each
        remaining pet's tasks are checked against the completion flag (O(n)).

        Args:
            completed: True for done tasks, False for pending, None for both.
            pet_name: Pet to restrict to (surrounding whitespace ignored), or
                None for all pets.

        Returns:
            Matching tasks in pet order, then insertion order.
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
        """Return tasks sorted chronologically by their "HH:MM" time (earliest first).

        Sorts on minutes since midnight rather than the raw string, so "9:00"
        correctly precedes "10:00". The sort is stable (ties keep input order)
        and does not mutate the input list.

        Raises:
            ValueError: If any task has an unparseable time.
        """
        return sorted(tasks, key=lambda t: _time_to_minutes(t.time))

    def detect_conflicts(self) -> List[str]:
        """Return a warning message for each group of pending tasks sharing a start time.

        Lightweight check: tasks conflict when they are pending, have the same
        due date, and start at the same "HH:MM" (durations are not compared).
        Works across pets as well as within one pet. Never raises for a task
        with an unparseable time; that task is skipped.

        Algorithm: bucket pending tasks in a dict keyed by (due_date, start
        minutes), then report every bucket holding 2+ tasks. Single pass plus
        a sort of the buckets, so O(n + k log k) for n tasks and k buckets.

        Returns:
            One warning string per conflicting bucket, ordered by date then
            time; empty list if there are no conflicts.
        """
        groups = defaultdict(list)
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.completed:
                    continue
                try:
                    start = _time_to_minutes(task.time)
                except ValueError:
                    continue
                groups[(task.due_date, start)].append((pet, task))

        warnings = []
        for (due, start), entries in sorted(groups.items()):
            if len(entries) < 2:
                continue
            hh, mm = divmod(start, 60)
            scope = "same pet" if len({p.name for p, _ in entries}) == 1 else "different pets"
            details = ", ".join(f"'{t.title}' ({p.name})" for p, t in entries)
            warnings.append(
                f"WARNING: {len(entries)} tasks at {hh:02d}:{mm:02d} "
                f"on {due} ({scope}): {details}"
            )
        return warnings

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
