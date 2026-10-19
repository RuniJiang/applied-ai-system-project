import datetime

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
    st.session_state.scheduler = Scheduler(st.session_state.owner)

owner = st.session_state.owner
scheduler = st.session_state.scheduler

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.subheader("Add a Pet")
col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if not pet_name.strip():
        st.error("Please enter a pet name.")
    elif any(p.name.lower() == pet_name.strip().lower() for p in owner.pets):
        st.warning(f"{pet_name} is already on your list.")
    else:
        owner.add_pet(Pet(name=pet_name.strip(), species=species))
        st.success(f"Added {pet_name}.")

if owner.pets:
    st.write("Your pets:")
    st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Schedule a Task")

if owner.pets:
    target_name = st.selectbox("For which pet?", [p.name for p in owner.pets])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        task_time = st.time_input("Time", value=datetime.time(8, 0))
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

    if st.button("Add task"):
        target_pet = next(p for p in owner.pets if p.name == target_name)
        scheduler.add_task(
            target_pet,
            Task(
                title=task_title,
                duration=int(duration),
                priority=priority,
                time=task_time.strftime("%H:%M"),
                frequency=frequency,
            ),
        )
        st.success(f"Added '{task_title}' for {target_name}.")
else:
    st.info("Add a pet before scheduling tasks.")

st.divider()

conflicts = scheduler.detect_conflicts()
all_tasks = owner.get_all_tasks()

st.subheader("Task Overview")
m1, m2, m3 = st.columns(3)
m1.metric("Pending", sum(not t.completed for t in all_tasks))
m2.metric("Completed", sum(t.completed for t in all_tasks))
m3.metric("Conflicts", len(conflicts))

if conflicts:
    st.warning(
        f"{len(conflicts)} scheduling conflict(s) found. "
        "Consider moving one of the tasks to a different time."
    )
    for warning in conflicts:
        st.warning(warning.removeprefix("WARNING: "), icon="⚠️")
elif all_tasks:
    st.success("No scheduling conflicts. You're all set!")

st.subheader("All Tasks")

if all_tasks:
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        pet_filter = st.selectbox("Pet", ["All"] + [p.name for p in owner.pets])
    with fcol2:
        status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])

    filtered = scheduler.filter_tasks(
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
        pet_name=None if pet_filter == "All" else pet_filter,
    )
    pet_obj_of = {id(t): p for p in owner.pets for t in p.tasks}
    ordered = scheduler.sort_by_time(filtered)

    if not ordered:
        st.info("No tasks match these filters.")
    else:
        st.caption(f"Showing {len(ordered)} task(s), sorted by time.")
        st.table(
            [
                {
                    "Time": t.time,
                    "Task": t.title,
                    "Pet": pet_obj_of[id(t)].name,
                    "Duration (min)": t.duration,
                    "Priority": t.priority.capitalize(),
                    "Frequency": t.frequency.capitalize(),
                    "Due": t.due_date.isoformat(),
                    "Status": "✅ Done" if t.completed else "⏳ Pending",
                }
                for t in ordered
            ]
        )

    pending = [t for t in ordered if not t.completed]
    if pending:
        labels = [
            f"{t.time} · {t.title} ({pet_obj_of[id(t)].name}, due {t.due_date})"
            for t in pending
        ]
        choice = st.selectbox("Mark a task complete", range(len(pending)), format_func=labels.__getitem__)
        if st.button("Mark complete"):
            t = pending[choice]
            next_task = scheduler.complete_task(pet_obj_of[id(t)], t)
            st.session_state.flash = (
                f"Completed '{t.title}'. Next {t.frequency} occurrence scheduled for {next_task.due_date}."
                if next_task
                else f"Completed '{t.title}'."
            )
            st.rerun()
else:
    st.info("No tasks yet. Add a pet and a task above.")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    schedule = scheduler.generate_schedule()
    if not schedule:
        st.info("No pending tasks to schedule.")
    else:
        pet_of = {id(t): p.name for p in owner.pets for t in p.tasks}
        st.success(f"Today's schedule for {owner.name}")
        if conflicts:
            st.warning(f"{len(conflicts)} conflict(s) detected. See the warnings above.")
        st.caption("Ordered by time, then priority.")
        st.table(
            [
                {
                    "time": t.time,
                    "task": t.title,
                    "pet": pet_of[id(t)],
                    "duration (min)": t.duration,
                    "priority": t.priority,
                    "frequency": t.frequency,
                }
                for t in schedule
            ]
        )
