from pawpal_system import Owner, Pet, Task, Scheduler

W = 56

def divider(char="-"): print(char * W)
def header(title, char="="): print(char * W); print(f"  {title}"); print(char * W)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=75)

mochi = Pet(name="Mochi", species="dog")
mochi.add_task(Task("Morning walk",   duration_minutes=30, priority="high",   frequency="daily"))
mochi.add_task(Task("Heartworm meds", duration_minutes=5,  priority="high",   frequency="daily"))
mochi.add_task(Task("Teeth brushing", duration_minutes=10, priority="medium", frequency="weekly"))
mochi.add_task(Task("Bath time",      duration_minutes=45, priority="low",    frequency="weekly"))

luna = Pet(name="Luna", species="cat")
luna.add_task(Task("Feed wet food",    duration_minutes=10, priority="high",   frequency="daily"))
luna.add_task(Task("Litter box clean", duration_minutes=10, priority="high",   frequency="daily"))
luna.add_task(Task("Brush coat",       duration_minutes=15, priority="medium", frequency="weekly"))
luna.add_task(Task("Enrichment play",  duration_minutes=20, priority="medium", frequency="as_needed"))

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner, day_start_hour=8)

# ---------------------------------------------------------------------------
# A — Full schedule (priority → frequency → duration tiebreaker)
# ---------------------------------------------------------------------------
header(f"TODAY'S SCHEDULE  —  {owner.name}  |  budget: {owner.available_minutes} min")
result = scheduler.generate_schedule()

print(f"\n{'TIME':<7} {'TASK':<22} {'MIN':>4}  {'PET':<6} {'PRIORITY':<8} FREQ")
divider()
for t in result.scheduled_tasks:
    print(f"  {t.start_time:<5} {t.title:<22} {t.duration_minutes:>4}  {t.pet_name:<6} {t.priority:<8} {t.frequency}")
divider()
print(f"  {'':5} {'Total time used:':<22} {result.total_minutes_used:>4} min")

# D — Conflicts
if result.conflict_tasks:
    print(f"\n  ⚠  CONFLICTS — high-priority tasks that didn't fit:")
    for t in result.conflict_tasks:
        print(f"     ! {t.title} ({t.duration_minutes} min) — free up time for this")

# Low-priority skips
if result.skipped_tasks:
    print(f"\n  Skipped (low/medium, did not fit):")
    for t in result.skipped_tasks:
        print(f"     - {t.title} ({t.duration_minutes} min) [{t.priority}]")

# ---------------------------------------------------------------------------
# B — Per-pet filtered view
# ---------------------------------------------------------------------------
header("PER-PET BREAKDOWN")
for pet in owner.pets:
    pet_result = result.filter_by_pet(pet.name)
    print(f"\n  {pet.name} the {pet.species}  ({pet_result.total_minutes_used} min):")
    for t in pet_result.scheduled_tasks:
        print(f"    {t.start_time}  {t.title} ({t.duration_minutes} min)")
    if not pet_result.scheduled_tasks:
        print("    (nothing scheduled)")

# ---------------------------------------------------------------------------
# C — Completed vs pending after marking two tasks done
# ---------------------------------------------------------------------------
header("MARK TASKS DONE  (C — filter by status)")

scheduler.mark_completed(mochi.tasks[0])   # Morning walk
scheduler.mark_completed(luna.tasks[0])    # Feed wet food

print(f"\n  Completed tasks:")
for t in owner.get_all_completed_tasks():
    print(f"    ✓  {t.title} ({t.pet_name})")

print(f"\n  Still pending:")
for t in owner.get_all_pending_tasks():
    print(f"    ○  {t.title} ({t.pet_name})")

# ---------------------------------------------------------------------------
# Auto-recurrence — completing a daily/weekly task spawns its next occurrence
# ---------------------------------------------------------------------------
header("AUTO-RECURRENCE — next occurrence on completion")

mochi_walk = mochi.tasks[0]   # Morning walk (daily)
luna_brush = luna.tasks[2]    # Brush coat (weekly)

next_walk  = scheduler.mark_completed(mochi_walk)
next_brush = scheduler.mark_completed(luna_brush)

print(f"\n  Completed:  '{mochi_walk.title}' and '{luna_brush.title}'")
print(f"\n  Auto-created next occurrences:")
print(f"    → {next_walk.title}  (daily)   due: {next_walk.due_date}")
print(f"    → {next_brush.title} (weekly)  due: {next_brush.due_date}")
print(f"\n  Mochi now has {len(mochi.tasks)} tasks ({sum(1 for t in mochi.tasks if not t.completed)} pending)")
print(f"  Luna  now has {len(luna.tasks)} tasks ({sum(1 for t in luna.tasks if not t.completed)} pending)")

# ---------------------------------------------------------------------------
# F — Time slots visible in a fresh schedule after recurrence
# ---------------------------------------------------------------------------
header("SCHEDULE AFTER RECURRENCE  (F — time slots)")

result2 = scheduler.generate_schedule()
print(f"\n{'TIME':<7} {'TASK':<22} {'MIN':>4}  {'PET'}")
divider()
for t in result2.scheduled_tasks:
    print(f"  {t.start_time:<5} {t.title:<22} {t.duration_minutes:>4}  {t.pet_name}")
divider("=")
