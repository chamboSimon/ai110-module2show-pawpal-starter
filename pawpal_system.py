from dataclasses import dataclass, field
from typing import List


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"


@dataclass
class Owner:
    name: str
    available_minutes: int


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    completed: bool = False


@dataclass
class ScheduleResult:
    scheduled_tasks: List[Task] = field(default_factory=list)
    skipped_tasks: List[Task] = field(default_factory=list)
    total_minutes_used: int = 0

    def summary(self) -> str:
        lines = []
        lines.append(f"Scheduled ({self.total_minutes_used} min used):")
        for task in self.scheduled_tasks:
            lines.append(f"  - {task.title} ({task.duration_minutes} min) [{task.priority}]")
        if self.skipped_tasks:
            lines.append("Skipped (did not fit in time budget):")
            for task in self.skipped_tasks:
                lines.append(f"  - {task.title} ({task.duration_minutes} min) [{task.priority}]")
        return "\n".join(lines)


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def generate_schedule(self) -> ScheduleResult:
        sorted_tasks = sorted(self.tasks, key=lambda t: _PRIORITY_ORDER.get(t.priority, 99))
        result = ScheduleResult()
        remaining = self.owner.available_minutes
        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                result.scheduled_tasks.append(task)
                result.total_minutes_used += task.duration_minutes
                remaining -= task.duration_minutes
            else:
                result.skipped_tasks.append(task)
        return result
