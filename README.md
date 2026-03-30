# PawPal+ (Module 2 Project)

PawPal+ is a Streamlit app that helps a pet owner plan daily care tasks for one or more pets. It goes beyond a simple to-do list: a smart scheduler ranks tasks by priority and frequency, enforces a time budget, detects schedule conflicts, and automatically queues the next occurrence of recurring tasks.

## Features

| Feature | Details |
|---|---|
| **Priority + frequency sort** | Tasks are ranked high → medium → low, then daily → weekly → as_needed. When two tasks are equal on both, the shorter one is scheduled first (greedy fit) |
| **Time-slot assignment** | Every scheduled task receives a concrete start time (e.g. `08:25`) counting forward from a configurable day-start hour |
| **Conflict warnings** | If two scheduled tasks have overlapping time windows, a yellow `⚠️` banner lists each overlap in plain English — the schedule is never silently broken |
| **High-priority conflict escalation** | A high-priority task that exceeds the remaining budget appears in a red `🚨` error banner rather than being silently skipped |
| **Auto-recurrence** | Completing a daily task spawns a new instance due tomorrow; completing a weekly task spawns one due in 7 days (`timedelta`) |
| **Per-pet tabs** | When multiple pets are registered, the schedule view splits into tabs — one per pet plus an "All pets" view |
| **Mark complete in UI** | One-click buttons mark tasks done and immediately show when the next occurrence was added |
| **Daily reset** | `Owner.reset_daily_tasks()` re-opens all daily tasks so the app is usable on day 2 without losing data |

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

The scheduler goes beyond a simple sorted list. Key features built into `pawpal_system.py`:

| Feature | How it works |
|---|---|
| **Priority + frequency sort** | Tasks are ranked high → medium → low, then daily → weekly → as_needed, then shortest-first as a tiebreaker to maximise tasks that fit the budget |
| **Per-pet filtering** | `Scheduler.get_schedule_for_pet(pet)` returns a filtered `ScheduleResult` showing only one pet's tasks and time used |
| **Status filtering** | `Owner.get_all_completed_tasks()` and `Pet.get_pending_tasks()` give distinct done vs. to-do views |
| **Conflict detection** | `Scheduler.detect_conflicts(tasks)` checks for overlapping time windows and returns plain-English warnings — it never crashes the program |
| **Auto-recurrence** | Completing a `daily` task spawns a new instance due tomorrow; completing a `weekly` task spawns one due in 7 days (`timedelta`) |
| **Time-slot assignment** | Each scheduled task is stamped with a `start_time` (e.g. `08:25`) counting forward from a configurable `day_start_hour` |
| **Daily reset** | `Owner.reset_daily_tasks()` clears `completed` on all daily tasks so the app is usable on day 2 without data loss |

Run `python main.py` to see all features demonstrated in the terminal.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

Run the full test suite with:

```bash
python3 -m pytest
```

The suite lives in `tests/test_pawpal.py` and covers 11 test cases across four areas:

| Area | What is verified |
|---|---|
| **Sorting correctness** | Scheduled tasks appear in ascending chronological (start-time) order; priority → frequency → duration sort keys all apply correctly |
| **Recurrence logic** | Completing a `daily` task spawns a new task due tomorrow; `weekly` spawns one due in 7 days; `as_needed` creates nothing |
| **Conflict detection** | Overlapping time windows produce a warning; adjacent tasks (end == start) produce no false positive; empty input is safe |
| **Budget enforcement** | A high-priority task that exceeds available minutes lands in `conflict_tasks`, not silently in `skipped_tasks` |

**Confidence level: ★★★★☆**
Core scheduling behaviors are well-covered. The greedy algorithm, recurrence, conflict detection, and priority ordering all pass. Edge cases around multi-pet schedules and calendar boundaries (month rollover) are not yet tested.
