# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
- core actions:
  - add a pet
  - schedule a walk
  - track pet care tasks
- Briefly describe your initial UML design.
  - It has four classes. An Owner has one or more Pets, and each Pet has Tasks. A Scheduler takes an Owner, pulls tasks from all of the owners's pets, and builds and displays a schedule.
- What classes did you include, and what responsibilities did you assign to each?
  - Owner: represents the person using the app. 
    - it holds 
      - name: owner's name
      - pets: their list of pets
    - it has functions/responsibilities:
      - add_pet(pet): registers a new pet
      - get_all_tasks: gathers the tasks from every pets
  - Pet: represents one animal. It stores pet's details, and owns its care tasks.
    - Details:
      - name
      - species
      - age
      - breed
      - tasks: pet's own list of tasks
    - Functions:
      - add_task(task)
      - remove_task(task)
  - Task: represents one care activity, such as walk, feeding, grooming.
    - Task attributes:
      - title
      - duration
      - priority
      - time: scheduled time
      - frequency
      - completed: flag for if the task is completed
    - function:
      - mark_complete(): update its status
  - Scheduler: is the planning logic. It holds a reference to the Owner
    - Attribute:
      - owner
    - Functions:
      - add_task(pet, task): attach a task to a pet
      - generate_schedule(): build an ordered list of tasks from the owner's pets
      - display_schedule(): shows that plan to the user

**b. Design changes**

- Did your design change during implementation?
  - yes. added a frequency in the task class
- If yes, describe at least one change and why you made it.
  - because each task may appears several times based on the frequency
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  - Time: each task has an "HH:MM" start time, and the schedule is ordered by it (parsed to minutes, so "9:00" sorts before "10:00").
  - Priority: high, medium or low breaks ties between tasks at the same time.
  - Due date and completion: `generate_schedule()` only includes pending tasks due today or earlier.
  - Recurrence: daily and weekly tasks spawn their next occurrence when completed.
  - Conflicts: pending tasks sharing the same date and start time are flagged as warnings.
  - Not considered: owner preferences and total time available in a day. Duration is stored and displayed but is not used to fit or drop tasks.
- How did you decide which constraints mattered most?
  - I started from what a pet owner needs: "what do I do, and when?" Time came first because a daily plan is a timeline. Priority came second as the tiebreaker, so the more important task is listed first when two are scheduled together. Due date and completion came next so the plan shows only what is actually left to do. I left out preferences and a daily time budget to keep the scheduler simple and testable.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  - `detect_conflicts()` only flags pending tasks that share the same due date and the exact same start time ("HH:MM"). It does not compare durations, so a 60-minute task at 09:00 and a task at 09:30 overlap in real life but are not reported.
- Why is that tradeoff reasonable for this scenario?
  - A pet owner mostly needs a quick heads-up that two things were scheduled at the same moment, and exact-match grouping is simple to read, easy to test, and runs in one pass over the tasks. Real overlap detection would need sorting by start time and tracking end times, which adds complexity for a small app where durations are rough estimates anyway. The check also never crashes: tasks with an unparseable time are skipped instead of raising, and it returns warnings rather than blocking the user from adding a task. Overlap detection is a natural next step if durations become more precise.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
  - Design brainstorming: I used AI to turn the scenario into a UML draft (Owner, Pet, Task, Scheduler) and then to convert that UML into class skeletons with docstrings and `pass` bodies.
  - Implementation: I had AI fill in the method bodies in small steps, then add a demo script (`main.py`), quick tests, one-line docstrings, and the README implementation summary.
- What kinds of prompts or questions were most helpful?
  - Small, specific prompts that referenced my own design, e.g. "implement the stubs from the UML", worked better than open-ended ones, because the output could be checked against the diagram.
  - Asking for a runnable demo right after the implementation was useful, since it showed the schedule output immediately.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
  - The AI's first version of `generate_schedule()` ordered tasks by time and priority. I did not take that as-is. Priority is stored as a string, and sorting those strings alphabetically gives "high", "low", "medium", which puts low priority ahead of medium. I kept the priority lookup (`PRIORITY_ORDER`) that maps high, medium and low to 0, 1 and 2, made it case-insensitive, and gave unknown values the lowest rank instead of raising an error.
  - I also kept the AI's `frequency` suggestion only after checking it against my UML. It was not in my original design, so I added it deliberately and recorded the change in section 1b. I kept `remove_task` safe (it does nothing if the task is missing) and made `Scheduler.add_task` register a new pet, so a task is never attached to a pet the owner doesn't know about.
- How did you evaluate or verify what the AI suggested?
  - I compared each class and method against my UML to confirm nothing was renamed or dropped.
  - I ran `python3 main.py` and checked the printed schedule by hand: tasks appear in time order, and ties are broken by priority.
  - I added quick tests in `tests/test_pawpal.py` and ran `pytest` so the behaviour is checked by code, not only by reading it.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
  - Task completion: `mark_complete()` flips the status.
  - Recurrence: completing a daily task creates a pending copy due the next day, and weekly and one-off tasks behave correctly.
  - Sorting: tasks come back in true chronological order, so "9:00" comes before "10:00".
  - Conflict detection: duplicate start times are flagged, and non-conflicting tasks are not.
  - Task management: adding a task increases the pet's task count.
- Why were these tests important?
  - They cover the logic the schedule depends on. A wrong sort or a missed recurrence would silently give the owner a bad plan. Sorting and recurrence also have easy-to-miss bugs (string comparison of times, date rollover), so a test catches them where reading the code might not.

**b. Confidence**

- How confident are you that your scheduler works correctly?
  - Fairly confident (4/5) for the core behaviors. All 7 tests pass, and I checked the demo output by hand. I am less sure about unusual input, since the tests cover mostly the normal path.
- What edge cases would you test next if you had more time?
  - Tasks with overlapping durations but different start times, which the current check does not catch.
  - Invalid or malformed times such as "25:00" or "abc". `detect_conflicts()` skips them, but `generate_schedule()` and `sort_by_time()` would raise.
  - Recurrence across month and year boundaries, and with mixed-case frequency such as "Daily".
  - Unknown priority values, an owner with no pets, and a pet with no tasks.
  - Completing the same recurring task twice, which would create duplicate next occurrences.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  - Designing the system as UML first and then building it in small steps. Because the classes had clear roles (Owner, Pet, Task, Scheduler), adding sorting, filtering, recurrence and conflict detection later did not require restructuring. I am also pleased that the logic layer is separate from the Streamlit UI, so the scheduler is easy to test on its own.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  - Replace exact-time conflict detection with real overlap detection that uses duration.
  - Use the owner's available time to decide which tasks fit in a day, and explain why tasks were included or dropped.
  - Store priority and frequency as enums instead of strings, so invalid values cannot get in.
  - Guard against completing the same recurring task twice.
  - Validate the time input in the UI and save data between sessions.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  - AI is fast at producing code, but I have to stay the architect. My UML gave me something concrete to check each suggestion against, and tests proved the behavior. The AI's first sort, which treated priority as a string, looked plausible but was wrong, and I only caught it because I checked the output. Small, specific prompts tied to my own design worked best.
