from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str   # "low", "medium", "high"
    frequency: str  # "daily", "weekly", "as_needed"
    completed: bool = False


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return a copy of all tasks belonging to this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> List[Task]:
        """Return only tasks that have not yet been marked completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all of this owner's pets, including completed ones."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def get_all_pending_tasks(self) -> List[Task]:
        """Return only incomplete tasks across all of this owner's pets."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks


@dataclass
class ScheduleResult:
    scheduled_tasks: List[Task] = field(default_factory=list)
    skipped_tasks: List[Task] = field(default_factory=list)
    total_minutes_used: int = 0
    label: str = ""  # e.g. "Mochi" or "Mochi, Buddy"

    def summary(self) -> str:
        """Return a formatted string listing scheduled and skipped tasks with time totals."""
        header = f"Daily plan for {self.label}" if self.label else "Daily plan"
        lines = [f"{header} ({self.total_minutes_used} min scheduled):"]
        for task in self.scheduled_tasks:
            lines.append(
                f"  - {task.title} ({task.duration_minutes} min)"
                f" [{task.priority}] [{task.frequency}]"
            )
        if self.skipped_tasks:
            lines.append("Skipped (did not fit in time budget):")
            for task in self.skipped_tasks:
                lines.append(
                    f"  - {task.title} ({task.duration_minutes} min)"
                    f" [{task.priority}] [{task.frequency}]"
                )
        return "\n".join(lines)


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_FREQUENCY_ORDER = {"daily": 0, "weekly": 1, "as_needed": 2}


class Scheduler:
    """Retrieves all pending tasks from the owner's pets and builds a daily plan."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all of the owner's pets (including completed)."""
        return self.owner.get_all_tasks()

    def get_pending_tasks(self) -> List[Task]:
        """Return only incomplete tasks across all of the owner's pets."""
        return self.owner.get_all_pending_tasks()

    def generate_schedule(self) -> ScheduleResult:
        """
        Greedy scheduler: sorts pending tasks by priority then frequency,
        selects tasks that fit within the owner's available_minutes budget.
        Daily high-priority tasks are always considered first.
        """
        pending = self.get_pending_tasks()
        sorted_tasks = sorted(
            pending,
            key=lambda t: (
                _PRIORITY_ORDER.get(t.priority, 99),
                _FREQUENCY_ORDER.get(t.frequency, 99),
            ),
        )

        label = ", ".join(p.name for p in self.owner.pets)
        result = ScheduleResult(label=label)
        remaining = self.owner.available_minutes

        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                result.scheduled_tasks.append(task)
                result.total_minutes_used += task.duration_minutes
                remaining -= task.duration_minutes
            else:
                result.skipped_tasks.append(task)

        return result

    def mark_completed(self, task: Task) -> None:
        """Mark a task as completed so it is excluded from future schedule runs."""
        task.completed = True
