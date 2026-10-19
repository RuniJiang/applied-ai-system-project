import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task(title="Walk", duration=30, priority="high", time="08:00")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feed", duration=10, priority="medium", time="09:00"))

    assert len(pet.tasks) == 1
