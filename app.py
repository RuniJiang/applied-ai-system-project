import datetime

import streamlit as st

from ai_planner import configure_logging, suggest_tasks
from pawpal_system import Owner, Pet, Task, Scheduler

configure_logging()

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.caption(
    "A pet care planner: add pets and tasks, get AI-suggested tasks grounded in "
    "care guidance, catch scheduling conflicts, and generate a daily schedule."
)


if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
    st.session_state.scheduler = Scheduler(st.session_state.owner)

owner = st.session_state.owner
scheduler = st.session_state.scheduler

tab_pets, tab_ai, tab_plan = st.tabs(["🐕 Pets & Tasks", "✨ AI Suggestions", "📋 Overview & Schedule"])

with tab_pets:
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


with tab_ai:
    st.subheader("AI Care Suggestions")
    st.caption(
        "Retrieves pet-care guidance for your pet's species and age, then asks Gemini to "
        "suggest tasks grounded in it. You review every suggestion before it is added."
    )
    if owner.pets:
        ai_name = st.selectbox("Suggest tasks for", [p.name for p in owner.pets], key="ai_pet")
        focus = st.text_input("What do you need help with?", value="daily exercise feeding grooming")
        if st.button("Get AI suggestions"):
            ai_pet = next(p for p in owner.pets if p.name == ai_name)
            with st.spinner("Retrieving guidance and planning..."):
                st.session_state.ai_result = (ai_name, suggest_tasks(ai_pet, focus, existing=ai_pet.tasks))

        if "ai_result" in st.session_state:
            res_name, res = st.session_state.ai_result
            if res.blocked:
                st.error(res.message)
            elif res.fallback:
                st.warning(res.message + " Add tasks manually above.")
            else:
                st.metric("Confidence", f"{res.confidence:.0%}")
                if res.confidence < 0.5:
                    st.warning("Low confidence: double-check these against your vet's advice.")
                picks = []
                for i, s in enumerate(res.suggestions):
                    if st.checkbox(
                        f"{s.time} · {s.title} ({s.duration} min, {s.priority}, {s.frequency})",
                        value=True, key=f"pick_{i}",
                    ):
                        picks.append(s)
                    st.caption(f"{s.reason}  \nSource: {s.source}")
                if res.rejected:
                    with st.expander(f"{len(res.rejected)} suggestion(s) rejected by guardrails"):
                        for r in res.rejected:
                            st.write("- " + r)
                if st.button("Add selected to schedule") and picks:
                    target = next(p for p in owner.pets if p.name == res_name)
                    for s in picks:
                        scheduler.add_task(target, s.to_task())
                    del st.session_state.ai_result
                    st.session_state.flash = f"Added {len(picks)} AI-suggested task(s) for {res_name}."
                    st.rerun()
            if res.passages and not res.blocked:
                with st.expander("Sources retrieved"):
                    for p in res.passages:
                        st.markdown(f"**{p.source}** (score {p.score})  \n{p.text}")
    else:
        st.info("Add a pet to get AI suggestions.")

with tab_plan:
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
