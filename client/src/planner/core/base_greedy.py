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
    from datetime import date, datetime, time
    from planner.core.utils import load_people, load_events

    people = load_people()
    events = load_events()

    client = people[0]
    day = date(2025, 8, 3)  # Arijit concert fixed at 17:00 on this date

    # Existing subset of events
    wanted_ids = {
        "e_st_lawrence_01",
        "e_rom_01",
        "e_ago_01",
        "e_distillery_01",
        "e_cn_tower_01",
        "e_concert_southasian_01",
    }
    subset = [e for e in events if e.id in wanted_ids]

    # --- NEW MOCK EVENT: Outdoor walk blocked by rain ---
    mock_rain_event = {
        "id": "e_mock_rain_01",
        "name": "Rainy Outdoor Stroll",
        "category": "walk",
        "tags": ["outdoor", "nature"],
        "venue": "Mock Park",
        "city": "Toronto",
        "location": {"lat": 43.650, "lng": -79.380},
        "duration_min": 60,
        "cost_cad": 0,
        "age_min": 0,
        "age_max": 99,
        "opening_hours": {"daily": ["08:00", "20:00"]},
        "fixed_times": [],
        "requires_booking": False,
        "weather_blockers": ["Slight rain", "Moderate rain", "Heavy rain"],  # blocked
        "popularity": 0.5
    }

    # Simulate rainy conditions for testing
    current_weather = "Heavy rain"

    # Add mock event to the subset
    subset.append(Activity(**mock_rain_event))

    # Filter events based on weather for the greedy algorithm (optional test)
    filtered_subset = [e for e in subset if current_weather not in getattr(e, "weather_blockers", [])]

    print("Subset BEFORE weather filter:")
    for e in subset:
        print(f"- {e.name} (weather blockers: {e.weather_blockers})")

    print("\nSubset AFTER weather filter:")
    for e in filtered_subset:
        print(f"- {e.name}")

    # Make the day plan (greedy algorithm should skip rainy event)
    plan = make_day_plan(client, filtered_subset, day)

    print(f"\nPlan for {day}:")
    for ev in plan.events:
        print(f"- {ev.start_dt.time()}–{ev.end_dt.time()}  {ev.activity.name} ({ev.activity.category})  ${ev.activity.cost_cad}")


# if __name__ == "__main__":
#     # Force the test day to the concert day
#     from datetime import date
#     from .utils import load_people, load_events
#
#     people = load_people()
#     events = load_events()
#
#     # Any client is fine; we hard-set the day
#     client = people[0]
#     day = date(2025, 8, 3)  # Arijit concert fixed at 17:00 on this date
#
#     # Carefully chosen set to pack the afternoon and force CN Tower into 16:30–18:00,
#     # which overlaps the concert. Optimized solver should nudge CN Tower to 19:30–21:00.
#     wanted_ids = {
#         "e_st_lawrence_01",          # 07:00–08:15 (Sat pattern; ok to keep early)
#         "e_rom_01",                  # 150m, daily 10:00–17:30 -> 10:00–12:30
#         "e_ago_01",                  # 120m, Sun 10:30–17:30 -> 12:30–14:30
#         "e_distillery_01",           # 90m, daily 10:00–21:00 -> 14:30–16:00
#         "e_cn_tower_01",             # 90m, daily until 21:00 -> earliest non-overlap ~16:30–18:00 (conflicts)
#         "e_concert_southasian_01",   # FIXED 17:00–19:30
#     }
#     subset = [e for e in events if e.id in wanted_ids]
#
#     plan = make_day_plan(client, subset, day)
#
#     print(f"Plan for {day}:")
#     for ev in plan.events:
#         print(f"- {ev.start_dt.time()}–{ev.end_dt.time()}  {ev.activity.name} ({ev.activity.category})  ${ev.activity.cost_cad}")
