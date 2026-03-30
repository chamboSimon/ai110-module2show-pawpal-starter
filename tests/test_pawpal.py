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
