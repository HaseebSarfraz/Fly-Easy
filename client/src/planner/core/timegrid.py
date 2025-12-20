# src/planner/core/timegrid.py
from datetime import date, datetime
from .models import Activity


def choose_step_minutes(act: Activity) -> int:
    d = act.duration_min
    if act.fixed_times:
        return 0  # unused
    if d >= 150:
        return 60
    if d >= 60:
        return 30
    return 15  # if the activity is < 60 minutes long then 15 min gap sounds reasonable. 


def generate_candidate_times(act: Activity, day: date, step_minutes: int = 60) -> list[datetime]:
    """
    For activities without fixed_times, return feasible start datetimes on `day`
    by stepping through the opening window in `step_minutes` increments.
    """
    if act.fixed_times:
        # fixed-times are exact; return those as datetimes
        out = []
        for ft in act.fixed_times:
            if ft.get("date") == day.isoformat():
                try:
                    hh, mm = ft["start"].split(":")
                    out.append(datetime(day.year, day.month, day.day, int(hh), int(mm)))
                except Exception:
                    pass
        return out

    window = act._window_for_date(day)
    if window is None:
        return []

    start_min, end_min = window
    # last feasible start is end_min - duration
    last_start = end_min - act.duration_min  # So the latest user can explore this activity 
    candidates = []  # other timeslots
    curr = start_min
    while curr <= last_start:
        hh, mm = divmod(curr, 60)
        candidates.append(datetime(day.year, day.month, day.day, hh, mm))
        curr += step_minutes
    return candidates
