import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — acts as the app's persistent memory across reruns.
# On the very first run these keys don't exist yet, so we create them once.
# Every subsequent rerun skips this block and reuses the existing objects.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None          # set after owner form is submitted
if "active_pet" not in st.session_state:
    st.session_state.active_pet = None     # the pet currently selected for tasks
if "last_result" not in st.session_state:
    st.session_state.last_result = None    # most recent ScheduleResult for mark-complete
if "last_scheduler" not in st.session_state:
    st.session_state.last_scheduler = None # Scheduler instance that produced last_result

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner & time budget")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Your name", value="Jordan")
    with col2:
        available_minutes = st.number_input(
            "Time available today (min)", min_value=10, max_value=480, value=90
        )
    submitted = st.form_submit_button("Save owner")

if submitted:
    if st.session_state.owner is None:
        st.session_state.owner = Owner(
            name=owner_name, available_minutes=int(available_minutes)
        )
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = int(available_minutes)
    st.success(f"Owner saved: {owner_name} ({available_minutes} min available)")

if st.session_state.owner is None:
    st.info("Fill in your name and time budget above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Add a pet")

with st.form("pet_form"):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    new_pet = Pet(name=pet_name, species=species)
    owner.add_pet(new_pet)
    st.session_state.active_pet = new_pet
    st.success(f"Added {pet_name} the {species}!")

if owner.pets:
    pet_names = [p.name for p in owner.pets]
    selected_name = st.selectbox("Select pet to add tasks to", pet_names)
    st.session_state.active_pet = next(p for p in owner.pets if p.name == selected_name)
else:
    st.info("No pets yet — add one above.")

# ---------------------------------------------------------------------------
# Section 3 — Add tasks to the selected pet
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Add tasks")

if st.session_state.active_pet is None:
    st.info("Add a pet first, then come back to add tasks.")
else:
    active_pet: Pet = st.session_state.active_pet
    st.markdown(f"Adding tasks for **{active_pet.name}**")

    with st.form("task_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            task_title = st.text_input("Task", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
        with col4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])
        add_task = st.form_submit_button("Add task")

    if add_task:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
        )
        active_pet.add_task(task)
        st.success(f"Added '{task_title}' to {active_pet.name}")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.markdown("**All tasks (across all pets):**")
        st.table(
            [
                {
                    "Pet": t.pet_name,
                    "Task": t.title,
                    "Min": t.duration_minutes,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Done": "✓" if t.completed else "",
                }
                for t in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Today's schedule")

all_tasks = owner.get_all_tasks()
if not all_tasks:
    st.info("Add at least one task before generating a schedule.")
else:
    if st.button("Generate schedule"):
        scheduler = Scheduler(owner)
        result = scheduler.generate_schedule()
        st.session_state.last_result = result
        st.session_state.last_scheduler = scheduler

    result = st.session_state.last_result
    scheduler = st.session_state.last_scheduler

    if result is not None:
        # ── Budget summary bar ──────────────────────────────────────────────
        used = result.total_minutes_used
        budget = owner.available_minutes
        remaining = budget - used
        st.subheader(f"Plan for {owner.name} — {used} / {budget} min used")
        st.progress(min(used / budget, 1.0))
        st.caption(f"{remaining} min remaining in budget")

        # ── Time-overlap warnings (soft conflicts) ──────────────────────────
        if result.overlap_warnings:
            st.warning(
                f"⚠️ **{len(result.overlap_warnings)} time overlap(s) detected** — "
                "tasks below were scheduled but their windows overlap. "
                "Consider adjusting durations or start times."
            )
            for w in result.overlap_warnings:
                st.markdown(f"- {w}")

        # ── Hard conflicts: high-priority tasks that didn't fit ─────────────
        if result.conflict_tasks:
            st.error(
                f"🚨 **{len(result.conflict_tasks)} high-priority task(s) could not be scheduled** — "
                "they exceeded your available time budget. Free up time or shorten other tasks."
            )
            for t in result.conflict_tasks:
                st.markdown(
                    f"- **{t.title}** ({t.pet_name}) — {t.duration_minutes} min "
                    f"[{t.priority}] [{t.frequency}]"
                )

        # ── Scheduled tasks table ───────────────────────────────────────────
        if result.scheduled_tasks:
            st.success(f"✅ {len(result.scheduled_tasks)} task(s) scheduled")

            # Per-pet tabs when there are multiple pets
            if len(owner.pets) > 1:
                tabs = st.tabs([p.name for p in owner.pets] + ["All pets"])
                pet_views = [result.filter_by_pet(p.name) for p in owner.pets]
                for tab, pet, pet_result in zip(tabs[:-1], owner.pets, pet_views):
                    with tab:
                        if pet_result.scheduled_tasks:
                            st.table(
                                [
                                    {
                                        "Start": t.start_time,
                                        "Task": t.title,
                                        "Min": t.duration_minutes,
                                        "Priority": t.priority,
                                        "Frequency": t.frequency,
                                    }
                                    for t in pet_result.scheduled_tasks
                                ]
                            )
                        else:
                            st.info(f"No tasks scheduled for {pet.name}.")
                with tabs[-1]:
                    _all_tab_tasks = result.scheduled_tasks
                    st.table(
                        [
                            {
                                "Start": t.start_time,
                                "Pet": t.pet_name,
                                "Task": t.title,
                                "Min": t.duration_minutes,
                                "Priority": t.priority,
                                "Frequency": t.frequency,
                            }
                            for t in _all_tab_tasks
                        ]
                    )
            else:
                st.table(
                    [
                        {
                            "Start": t.start_time,
                            "Task": t.title,
                            "Min": t.duration_minutes,
                            "Priority": t.priority,
                            "Frequency": t.frequency,
                        }
                        for t in result.scheduled_tasks
                    ]
                )

            # ── Mark tasks complete ─────────────────────────────────────────
            st.markdown("---")
            st.markdown("**Mark tasks complete:**")
            for t in result.scheduled_tasks:
                if not t.completed:
                    label = f"Complete: {t.title} ({t.pet_name}, {t.start_time})"
                    if st.button(label, key=f"complete_{id(t)}"):
                        next_task = scheduler.mark_completed(t)
                        if next_task:
                            st.success(
                                f"✓ '{t.title}' marked done. "
                                f"Next {t.frequency} occurrence added for {next_task.due_date}."
                            )
                        else:
                            st.success(f"✓ '{t.title}' marked done.")
                        st.rerun()
                else:
                    st.markdown(f"~~{t.title}~~ ✓ ({t.pet_name})")

        else:
            st.warning("No tasks fit within your time budget.")

        # ── Skipped tasks ───────────────────────────────────────────────────
        if result.skipped_tasks:
            with st.expander(f"Skipped tasks ({len(result.skipped_tasks)}) — did not fit in budget"):
                for t in result.skipped_tasks:
                    st.markdown(
                        f"- **{t.title}** ({t.pet_name}) — {t.duration_minutes} min "
                        f"[{t.priority}] [{t.frequency}]"
                    )
