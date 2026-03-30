from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str            # "low", "medium", "high"
    frequency: str           # "daily", "weekly", "as_needed"
    completed: bool = False
    pet_name: str = ""       # stamped automatically by Pet.add_task()
    start_time: str = ""     # assigned by Scheduler when time slots are built
    due_date: Optional[date] = None  # None = due today; future date = not yet due


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list and stamp its pet_name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return a copy of all tasks belonging to this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> List[Task]:
        """Return incomplete tasks whose due_date is today or earlier (or unset)."""
        today = date.today()
        return [
            t for t in self.tasks
            if not t.completed and (t.due_date is None or t.due_date <= today)
        ]

    def get_completed_tasks(self) -> List[Task]:
        """Return only tasks that have been marked completed."""
        return [t for t in self.tasks if t.completed]


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

    def get_all_completed_tasks(self) -> List[Task]:
        """Return completed tasks across all of this owner's pets."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_completed_tasks())
        return tasks

    def reset_daily_tasks(self) -> int:
        """Reset completed=False for every daily-frequency task. Returns count reset."""
        count = 0
        for task in self.get_all_tasks():
            if task.frequency == "daily" and task.completed:
                task.completed = False
                count += 1
        return count


@dataclass
class ScheduleResult:
    scheduled_tasks: List[Task] = field(default_factory=list)
    skipped_tasks: List[Task] = field(default_factory=list)
    conflict_tasks: List[Task] = field(default_factory=list)  # high-priority tasks that didn't fit
    overlap_warnings: List[str] = field(default_factory=list) # time-overlap warnings from detect_conflicts
    total_minutes_used: int = 0
    label: str = ""

    def filter_by_pet(self, pet_name: str) -> "ScheduleResult":
        """Return a new ScheduleResult containing only tasks belonging to pet_name."""
        return ScheduleResult(
            scheduled_tasks=[t for t in self.scheduled_tasks if t.pet_name == pet_name],
            skipped_tasks=[t for t in self.skipped_tasks if t.pet_name == pet_name],
            conflict_tasks=[t for t in self.conflict_tasks if t.pet_name == pet_name],
            total_minutes_used=sum(
                t.duration_minutes
                for t in self.scheduled_tasks
                if t.pet_name == pet_name
            ),
            label=pet_name,
        )

    def summary(self) -> str:
        """Return a formatted string listing scheduled, overlap warnings, conflicts, and skipped tasks."""
        header = f"Daily plan for {self.label}" if self.label else "Daily plan"
        lines = [f"{header} ({self.total_minutes_used} min scheduled):"]
        for task in self.scheduled_tasks:
            slot = f" @ {task.start_time}" if task.start_time else ""
            lines.append(
                f"  - {task.title}{slot} ({task.duration_minutes} min)"
                f" [{task.priority}] [{task.frequency}]"
            )
        if self.overlap_warnings:
            lines.append("TIME OVERLAPS detected:")
            for w in self.overlap_warnings:
                lines.append(f"  ⚠  {w}")
        if self.conflict_tasks:
            lines.append("CONFLICTS — high-priority tasks that did not fit:")
            for task in self.conflict_tasks:
                lines.append(
                    f"  ! {task.title} ({task.duration_minutes} min)"
                    f" — consider freeing up time"
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

    def __init__(self, owner: Owner, day_start_hour: int = 8):
        self.owner = owner
        self.day_start_hour = day_start_hour  # hour the day begins, used for time-slot assignment

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all of the owner's pets (including completed)."""
        return self.owner.get_all_tasks()

    def get_pending_tasks(self) -> List[Task]:
        """Return only incomplete tasks across all of the owner's pets."""
        return self.owner.get_all_pending_tasks()

    def generate_schedule(self) -> ScheduleResult:
        """
        Greedy scheduler: sorts by priority, then frequency, then duration (shorter first
        as tiebreaker). Assigns sequential start times from day_start_hour. Flags any
        skipped high-priority task as a conflict rather than a silent skip.
        """
        pending = self.get_pending_tasks()
        # A — duration is third sort key: shorter tasks fill remaining budget more efficiently
        sorted_tasks = sorted(
            pending,
            key=lambda t: (
                _PRIORITY_ORDER.get(t.priority, 99),
                _FREQUENCY_ORDER.get(t.frequency, 99),
                t.duration_minutes,
            ),
        )

        label = ", ".join(p.name for p in self.owner.pets)
        result = ScheduleResult(label=label)
        remaining = self.owner.available_minutes
        current_minutes = self.day_start_hour * 60  # F — running clock in minutes from midnight

        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                # F — stamp start time on the task object
                h, m = divmod(current_minutes, 60)
                task.start_time = f"{h:02d}:{m:02d}"
                current_minutes += task.duration_minutes
                remaining -= task.duration_minutes
                result.scheduled_tasks.append(task)
                result.total_minutes_used += task.duration_minutes
            else:
                # D — high-priority skips become conflicts, not silent drops
                if task.priority == "high":
                    result.conflict_tasks.append(task)
                else:
                    result.skipped_tasks.append(task)

        result.overlap_warnings = self.detect_conflicts(result.scheduled_tasks)
        return result

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """
        Check a list of timed tasks for overlapping windows. Returns warning strings
        rather than raising, so callers can surface them without crashing.

        Overlap condition: task A starts before task B ends AND task B starts before task A ends.
        Only tasks that have a start_time set are checked.

        Tradeoff: checks exact numeric overlap, not human intent — a 5-min walk at 08:00
        and a 5-min feeding at 08:03 will be flagged even if a real owner could do both.
        """
        def to_min(t: str) -> int:
            h, m = map(int, t.split(":"))
            return h * 60 + m

        def fmt(minutes: int) -> str:
            return f"{minutes // 60:02d}:{minutes % 60:02d}"

        timed = [(t, to_min(t.start_time)) for t in tasks if t.start_time]
        warnings: List[str] = []

        for i, (a, start_a) in enumerate(timed):
            end_a = start_a + a.duration_minutes
            for b, start_b in timed[i + 1:]:
                end_b = start_b + b.duration_minutes
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        f"'{a.title}' ({a.pet_name}, {a.start_time}–{fmt(end_a)}) "
                        f"overlaps '{b.title}' ({b.pet_name}, {b.start_time}–{fmt(end_b)})"
                    )
        return warnings

    def get_schedule_for_pet(self, pet: Pet) -> ScheduleResult:
        """Run a full schedule then return only the entries belonging to pet."""
        return self.generate_schedule().filter_by_pet(pet.name)  # B

    def mark_completed(self, task: Task) -> Optional[Task]:
        """
        Mark a task as completed. For daily/weekly tasks, automatically creates and
        registers the next occurrence on the owning pet using timedelta. Returns the
        new Task if one was created, otherwise None.
        """
        task.completed = True

        if task.frequency not in ("daily", "weekly"):
            return None

        delta = timedelta(days=1) if task.frequency == "daily" else timedelta(weeks=1)
        next_due = date.today() + delta

        next_task = Task(
            title=task.title,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            frequency=task.frequency,
            due_date=next_due,
        )

        # find the pet that owns this task and register the next occurrence
        pet = next((p for p in self.owner.pets if task in p.tasks), None)
        if pet:
            pet.add_task(next_task)

        return next_task
