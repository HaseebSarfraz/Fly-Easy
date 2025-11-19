# src/planner/core/solver.py
from datetime import date, datetime, timedelta
from typing import List
from planner.core.models import Client, Activity, PlanDay, PlanEvent
from planner.core.constraints import hard_feasible, hc_open_window_ok, hc_age_ok
from planner.core.timegrid import generate_candidate_times, choose_step_minutes
from planner.core.scoring import interest_score
from planner.core.utils import to_minutes

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
            
            # Checks if the age restriction and start time is feasible based on 
            # when client starts and the duration of the activity with respect to its closing time
            age_feasibility = hc_age_ok(client, act)
            time_window = hc_open_window_ok(act, start_dt)
            
            # Checks for time overlap between this new activity and any of the planned acts
            fits_no_overlap = fits_no_overlap(plan.events, start_dt, act) 
                
            if not age_feasibility:
                continue

            if not time_window: 
                # So since time_window was false then it means we are starting 
                # at a time thats either before opening, or by the time we'll finish the
                # activity it will exceed the closing time. 
                continue

            if not fits_no_overlap:
                # Repair A: 
                # We can try to find more time slots for this activity 
                # If we find a time slot that works for B then we can check other
                # hard constraints again and then place Activity B in the plan
                act_end_time = None
                if "daily" in act.opening_hours:
                    act_end_time = act.opening_hours["daily"][1]

                else: 
                    act_end_time = act.opening_hours[day.day]

                adjusted = False
                step += choose_step_minutes(act)
                while step < to_minutes(act_end_time):

                    for start_dt in generate_candidate_times(act, day, step):
                        if hard_feasible(client, act, start_dt) and fits_no_overlap(plan.events, start_dt, act):
                            plan.add(PlanEvent(act, start_dt))
                            adjusted = True
                            break  # We have adjusted actiivty B
                    step += choose_step_minutes(act)

                if not adjusted: # Repair A didn't work

                # If above doesn't work then Repair B: 
                # We see what is activity is B conflicting with
                # If its only 1 activity, we try to move that activityA around.
                # If that activity gets fit somewhere else, then we keep B where we were
                # putting it initally. 

                # If activityA is not fitting any where else then we revert it back to 
                # where it was and drop activityB because actiivtyA appeared first so it obv
                # had a better interest rating so we keep it. 
                
               

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
