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


def test_add_task_increases_pet_task_count():
    """add_task() should increase the pet's task list by one each time."""
    pet = Pet(name="Luna", species="cat")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feed wet food", duration_minutes=10, priority="high", frequency="daily"))
    assert len(pet.tasks) == 1

    pet.add_task(Task(title="Brush coat", duration_minutes=15, priority="medium", frequency="weekly"))
    assert len(pet.tasks) == 2
