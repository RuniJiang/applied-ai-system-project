"""Temporary testing ground for the PawPal+ logic layer."""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Runi")
    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
    luna = Pet(name="Luna", species="cat", breed="Tabby", age=5)

    scheduler = Scheduler(owner)
    scheduler.add_task(mochi, Task("Morning walk", 30, "high", "07:30", "daily"))
    scheduler.add_task(luna, Task("Breakfast", 10, "high", "08:00", "daily"))
    scheduler.add_task(mochi, Task("Flea medication", 5, "medium", "12:00", "weekly"))
    scheduler.add_task(luna, Task("Play session", 20, "low", "18:00", "daily"))

    scheduler.display_schedule()


if __name__ == "__main__":
    main()
