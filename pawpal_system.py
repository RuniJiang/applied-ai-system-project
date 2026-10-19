"""PawPal+ logic layer: classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field
from typing import List

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    title: str  # description of the activity
    duration: int  # minutes
    priority: str  # e.g. "low", "medium", "high"
    time: str  # e.g. "08:00"
    frequency: str = "once"  # e.g. "once", "daily", "weekly"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


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
        self.owner = owner

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a task to the given pet (adding the pet to the owner if new)."""
        if pet not in self.owner.pets:
            self.owner.add_pet(pet)
        pet.add_task(task)

    def generate_schedule(self) -> List[Task]:
        """Return all of the owner's pending tasks, ordered by time then priority."""
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        return sorted(
            pending,
            key=lambda t: (t.time, PRIORITY_ORDER.get(t.priority.lower(), len(PRIORITY_ORDER))),
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
