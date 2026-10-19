"""Temporary testing ground for the PawPal+ logic layer."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(heading: str, tasks: list) -> None:
    """Print a heading followed by one line per task."""
    print(f"\n{heading}")
    if not tasks:
        print("  (none)")
    for t in tasks:
        status = "done" if t.completed else "pending"
        print(f"  {t.time:>5}  {t.title} - {t.priority}, {status}")


def main() -> None:
    owner = Owner(name="Runi")
    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
    luna = Pet(name="Luna", species="cat", breed="Tabby", age=5)

    scheduler = Scheduler(owner)
    # Added deliberately out of chronological order (note "9:00" vs "10:00").
    morning_walk = Task("Morning walk", 30, "high", "07:30", "daily")
    breakfast = Task("Breakfast", 10, "high", "9:00", "daily")
    scheduler.add_task(luna, Task("Play session", 20, "low", "18:00", "daily"))
    scheduler.add_task(mochi, Task("Flea medication", 5, "medium", "12:00", "weekly"))
    scheduler.add_task(luna, Task("Vet call", 15, "high", "10:00", "once"))
    scheduler.add_task(mochi, morning_walk)
    scheduler.add_task(luna, breakfast)
    scheduler.add_task(mochi, Task("Evening walk", 30, "medium", "17:00", "daily"))

    # Complete a couple so the completion filter has something to show.
    # Daily tasks automatically spawn a new instance due tomorrow.
    scheduler.complete_task(mochi, morning_walk)
    scheduler.complete_task(luna, breakfast)

    all_tasks = scheduler.filter_tasks()
    print_tasks("Insertion order (unsorted):", all_tasks)
    print_tasks("All tasks sorted by time:", scheduler.sort_by_time(all_tasks))

    print_tasks(
        "Pending only, sorted:",
        scheduler.sort_by_time(scheduler.filter_tasks(completed=False)),
    )
    print_tasks(
        "Completed only:",
        scheduler.sort_by_time(scheduler.filter_tasks(completed=True)),
    )
    print_tasks(
        "Mochi's tasks, sorted:",
        scheduler.sort_by_time(scheduler.filter_tasks(pet_name="mochi")),
    )
    print_tasks(
        "Luna's pending tasks, sorted:",
        scheduler.sort_by_time(scheduler.filter_tasks(completed=False, pet_name="Luna")),
    )
    print_tasks("Unknown pet:", scheduler.filter_tasks(pet_name="Rex"))

    print()
    scheduler.display_schedule()


if __name__ == "__main__":
    main()
