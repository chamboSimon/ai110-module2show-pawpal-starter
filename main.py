from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog")
mochi.add_task(Task("Morning walk",    duration_minutes=30, priority="high",   frequency="daily"))
mochi.add_task(Task("Heartworm meds",  duration_minutes=5,  priority="high",   frequency="daily"))
mochi.add_task(Task("Teeth brushing",  duration_minutes=10, priority="medium", frequency="weekly"))
mochi.add_task(Task("Bath time",       duration_minutes=45, priority="low",    frequency="weekly"))

luna = Pet(name="Luna", species="cat")
luna.add_task(Task("Feed wet food",    duration_minutes=10, priority="high",   frequency="daily"))
luna.add_task(Task("Litter box clean", duration_minutes=10, priority="high",   frequency="daily"))
luna.add_task(Task("Brush coat",       duration_minutes=15, priority="medium", frequency="weekly"))
luna.add_task(Task("Enrichment play",  duration_minutes=20, priority="medium", frequency="as_needed"))

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Schedule ---
scheduler = Scheduler(owner)
result = scheduler.generate_schedule()

# --- Display ---
WIDTH = 52
print("=" * WIDTH)
print(f"  TODAY'S SCHEDULE  —  {owner.name}'s pets")
print(f"  Time budget: {owner.available_minutes} min")
print("=" * WIDTH)

if result.scheduled_tasks:
    print(f"\n{'TASK':<28} {'MIN':>4}  {'PRIORITY':<8} FREQ")
    print("-" * WIDTH)
    for task in result.scheduled_tasks:
        print(f"  {task.title:<26} {task.duration_minutes:>4}  {task.priority:<8} {task.frequency}")
    print("-" * WIDTH)
    print(f"  {'Total time used:':<26} {result.total_minutes_used:>4} min")
else:
    print("\n  No tasks fit within the time budget.")

if result.skipped_tasks:
    print(f"\n  SKIPPED (did not fit in {owner.available_minutes}-min budget):")
    for task in result.skipped_tasks:
        print(f"    - {task.title} ({task.duration_minutes} min) [{task.priority}]")

print("=" * WIDTH)
