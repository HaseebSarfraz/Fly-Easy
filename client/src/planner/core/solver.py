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
    from .utils import load_people, load_events
    people = load_people()
    events = load_events()
    client = people[0]
    day = client.trip_start

    subset = [e for e in events if e.category in {"museum","food","walk","viewpoint"}][:8]
    plan = make_day_plan(client, subset, day)

    print(f"Plan for {day}:")
    for ev in plan.events:
        print(f"- {ev.start_dt.time()}–{ev.end_dt.time()}  {ev.activity.name} ({ev.activity.category})  ${ev.activity.cost_cad}")
