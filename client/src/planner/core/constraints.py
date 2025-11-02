# src/planner/core/constraints.py
from datetime import datetime
from .models import Client, Activity

def hc_age_ok(client: Client, act: "Activity") -> bool:
    return client.min_age() >= act.age_min and client.min_age() <= act.age_max

def hc_open_window_ok(act: "Activity", start_dt: datetime) -> bool:
    return act.can_start_at(start_dt)

def hard_feasible(client: Client, act: "Activity", start_dt: datetime) -> bool:
    return hc_age_ok(client, act) and hc_open_window_ok(act, start_dt)
