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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
