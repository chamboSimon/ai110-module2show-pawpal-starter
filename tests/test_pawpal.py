from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


def test_mark_completed_changes_task_status():
    """mark_completed() should flip task.completed from False to True."""
    owner = Owner(name="Jordan", available_minutes=60)
    task = Task(title="Morning walk", duration_minutes=30, priority="high", frequency="daily")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    assert task.completed is False
    scheduler.mark_completed(task)
    assert task.completed is True


def test_daily_task_creates_next_occurrence_on_completion():
    """Completing a daily task should spawn a new task due tomorrow on the same pet."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Morning walk", duration_minutes=30, priority="high", frequency="daily")
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    next_task = scheduler.mark_completed(task)

    assert next_task is not None
    assert next_task.title == "Morning walk"
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.completed is False
    assert len(pet.tasks) == 2  # original (done) + new occurrence


def test_weekly_task_creates_next_occurrence_due_in_seven_days():
    """Completing a weekly task should spawn a new task due in 7 days."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet(name="Luna", species="cat")
    task = Task(title="Brush coat", duration_minutes=15, priority="medium", frequency="weekly")
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    next_task = scheduler.mark_completed(task)

    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(weeks=1)
    assert next_task.completed is False


def test_as_needed_task_does_not_create_next_occurrence():
    """Completing an as_needed task should not auto-spawn a follow-up."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Vet visit", duration_minutes=60, priority="high", frequency="as_needed")
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    result = scheduler.mark_completed(task)

    assert result is None
    assert len(pet.tasks) == 1  # no new task added


def test_add_task_increases_pet_task_count():
    """add_task() should increase the pet's task list by one each time."""
    pet = Pet(name="Luna", species="cat")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feed wet food", duration_minutes=10, priority="high", frequency="daily"))
    assert len(pet.tasks) == 1

    pet.add_task(Task(title="Brush coat", duration_minutes=15, priority="medium", frequency="weekly"))
    assert len(pet.tasks) == 2


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_schedule_tasks_are_in_chronological_start_time_order():
    """Scheduled tasks should have ascending start_time values (chronological order)."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Buddy", species="dog")
    # Add tasks in reverse priority so the sort must reorder them
    pet.add_task(Task(title="Low walk",    duration_minutes=10, priority="low",    frequency="as_needed"))
    pet.add_task(Task(title="Med feed",    duration_minutes=15, priority="medium", frequency="daily"))
    pet.add_task(Task(title="High meds",   duration_minutes=5,  priority="high",   frequency="daily"))
    owner.add_pet(pet)

    result = Scheduler(owner).generate_schedule()

    # Extract start times as (hour, minute) tuples for clean comparison
    times = []
    for t in result.scheduled_tasks:
        h, m = map(int, t.start_time.split(":"))
        times.append((h, m))

    assert times == sorted(times), (
        f"Expected ascending start times but got: {[t.start_time for t in result.scheduled_tasks]}"
    )


def test_sorting_respects_priority_then_frequency_then_duration():
    """
    With equal available time, the first scheduled task must be the highest-priority,
    highest-frequency, shortest task — confirming all three sort keys work together.
    """
    owner = Owner(name="Alex", available_minutes=200)
    pet = Pet(name="Buddy", species="dog")

    # These three tasks share the same priority+frequency; the 5-min one should go first
    pet.add_task(Task(title="Long high daily",   duration_minutes=30, priority="high", frequency="daily"))
    pet.add_task(Task(title="Short high daily",  duration_minutes=5,  priority="high", frequency="daily"))
    # Lower priority — must come after both high-priority tasks
    pet.add_task(Task(title="Medium weekly",     duration_minutes=10, priority="medium", frequency="weekly"))
    owner.add_pet(pet)

    result = Scheduler(owner).generate_schedule()
    titles = [t.title for t in result.scheduled_tasks]

    assert titles[0] == "Short high daily", f"Expected shortest high-daily first, got: {titles}"
    assert titles[1] == "Long high daily",  f"Expected long high-daily second, got: {titles}"
    assert titles[2] == "Medium weekly",    f"Expected medium-weekly last, got: {titles}"


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks whose time windows overlap must produce a warning."""
    # Manually stamp start_time so we control the exact overlap
    task_a = Task(title="Walk",  duration_minutes=30, priority="high",   frequency="daily",   start_time="08:00")
    task_b = Task(title="Feed",  duration_minutes=20, priority="medium", frequency="daily",   start_time="08:15")
    task_a.pet_name = "Buddy"
    task_b.pet_name = "Buddy"

    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Buddy", species="dog")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_conflicts([task_a, task_b])

    assert len(warnings) == 1, f"Expected 1 overlap warning, got {len(warnings)}: {warnings}"
    assert "Walk" in warnings[0] and "Feed" in warnings[0]


def test_detect_conflicts_no_warning_for_adjacent_tasks():
    """Tasks that touch (end == start) are NOT overlapping and must produce no warning."""
    task_a = Task(title="Walk",  duration_minutes=30, priority="high",   frequency="daily",   start_time="08:00")
    task_b = Task(title="Feed",  duration_minutes=20, priority="medium", frequency="daily",   start_time="08:30")
    task_a.pet_name = "Buddy"
    task_b.pet_name = "Buddy"

    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Buddy", species="dog")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_conflicts([task_a, task_b])

    assert warnings == [], f"Expected no warnings for adjacent tasks but got: {warnings}"


def test_detect_conflicts_empty_list_returns_no_warnings():
    """detect_conflicts([]) should return an empty list without raising."""
    owner = Owner(name="Alex", available_minutes=60)
    owner.add_pet(Pet(name="Buddy", species="dog"))
    scheduler = Scheduler(owner)

    assert scheduler.detect_conflicts([]) == []


def test_high_priority_task_that_does_not_fit_goes_to_conflict_tasks():
    """A high-priority task that exceeds the time budget must appear in conflict_tasks, not skipped_tasks."""
    owner = Owner(name="Alex", available_minutes=10)  # only 10 min available
    pet = Pet(name="Buddy", species="dog")
    pet.add_task(Task(title="Long walk", duration_minutes=60, priority="high", frequency="daily"))
    owner.add_pet(pet)

    result = Scheduler(owner).generate_schedule()

    assert any(t.title == "Long walk" for t in result.conflict_tasks), (
        "High-priority task that didn't fit should be in conflict_tasks"
    )
    assert not any(t.title == "Long walk" for t in result.skipped_tasks), (
        "High-priority task must not silently end up in skipped_tasks"
    )
