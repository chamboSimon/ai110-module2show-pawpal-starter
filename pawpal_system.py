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
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def generate_schedule(self) -> ScheduleResult:
        pass
