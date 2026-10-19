"""PawPal+ logic layer: skeleton classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    title: str
    duration: int  # minutes
    priority: str  # e.g. "low", "medium", "high"
    time: str  # e.g. "08:00"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        pass


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across all of this owner's pets."""
        pass


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a task to the given pet."""
        pass

    def generate_schedule(self) -> List[Task]:
        """Build an ordered list of tasks for the owner's pets."""
        pass

    def display_schedule(self) -> None:
        """Print the generated schedule."""
        pass
