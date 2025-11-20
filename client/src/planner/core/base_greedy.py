# src/planner/core/solver.py
from datetime import date, datetime, timedelta
from typing import List
from planner.core.models import Client, Activity, PlanDay, PlanEvent
from planner.core.constraints import hard_feasible
from planner.core.timegrid import generate_candidate_times, choose_step_minutes
from planner.core.scoring import interest_score

def overlaps(a_start, a_end, b_start, b_end) -> bool:
    return not (a_end <= b_start or b_end <= a_start)

def fits_no_overlap(events: List[PlanEvent], start_dt: datetime, act: Activity) -> bool:
    end_dt = start_dt + timedelta(minutes=act.duration_min)
    for ev in events:
        if overlaps(start_dt, end_dt, ev.start_dt, ev.end_dt):
            return False
    return True

def make_day_plan(client: Client, activities: List[Activity], day: date) -> PlanDay:
    plan = PlanDay(day)

    # higher interest, then popularity
    acts_sorted = sorted(
        activities,
        key=lambda a: (interest_score(client, a), a.popularity),
        reverse=True,
    )

    for act in acts_sorted:
        step = choose_step_minutes(act) or 60
        for start_dt in generate_candidate_times(act, day, step_minutes=step):
            if hard_feasible(client, act, start_dt) and fits_no_overlap(plan.events, start_dt, act):
                plan.add(PlanEvent(act, start_dt))
                break  # first feasible slot for this activity

    return plan

if __name__ == "__main__":
    # Force the test day to the concert day
    from datetime import date
    from .utils import load_people, load_events

    people = load_people()
    events = load_events()

    # Any client is fine; we hard-set the day
    client = people[0]
    day = date(2025, 8, 3)  # Arijit concert fixed at 17:00 on this date

    # Carefully chosen set to pack the afternoon and force CN Tower into 16:30–18:00,
    # which overlaps the concert. Optimized solver should nudge CN Tower to 19:30–21:00.
    wanted_ids = {
        "e_st_lawrence_01",          # 07:00–08:15 (Sat pattern; ok to keep early)
        "e_rom_01",                  # 150m, daily 10:00–17:30 -> 10:00–12:30
        "e_ago_01",                  # 120m, Sun 10:30–17:30 -> 12:30–14:30
        "e_distillery_01",           # 90m, daily 10:00–21:00 -> 14:30–16:00
        "e_cn_tower_01",             # 90m, daily until 21:00 -> earliest non-overlap ~16:30–18:00 (conflicts)
        "e_concert_southasian_01",   # FIXED 17:00–19:30
    }
    subset = [e for e in events if e.id in wanted_ids]

    plan = make_day_plan(client, subset, day)

    print(f"Plan for {day}:")
    for ev in plan.events:
        print(f"- {ev.start_dt.time()}–{ev.end_dt.time()}  {ev.activity.name} ({ev.activity.category})  ${ev.activity.cost_cad}")
