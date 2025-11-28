# src/planner/core/solver.py
from datetime import date, datetime, timedelta, time      # MAKE SURE THIS IS INSTALLED
from typing import List                             # MAKE SURE THIS IS INSTALLED
from planner.core.models import Client, Activity, PlanDay, PlanEvent, Location
from planner.core.constraints import hard_feasible, hc_open_window_ok, hc_age_ok
from planner.core.timegrid import generate_candidate_times, choose_step_minutes
from planner.core.scoring import interest_score_age
from planner.core.utils import to_minutes

import requests                 # TO MAKE API REQUESTS (MUST BE INSTALLED ON DEVICE)
import pandas as pd             # MAKE SURE THIS IS INSTALLED ON THE DEVICE

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    99: "Heavy hail thunderstorm",
}


def overlaps(a_start, a_end, b_start, b_end) -> bool:
    return not (a_end <= b_start or b_end <= a_start)


def fits_no_overlap(events: List[PlanEvent], start_dt: datetime, act: Activity) -> bool:
    end_dt = start_dt + timedelta(minutes=act.duration_min)
    for ev in events:
        if overlaps(start_dt, end_dt, ev.start_dt, ev.end_dt):
            return False
    return True


def is_weather_suitable(activity: Activity, start_dt: datetime) -> bool:
    """
    Checks if the current <activity> is suitable to attend with the current weather.
    Return: true if the current activity will not be affected by the weather, false otherwise.
    """
    try:
        print(start_dt)
        wb = activity.weather_blockers
        end_dt = start_dt + timedelta(minutes=activity.duration_min)
        if not wb:
            return True

        # TO GET THE TIMEZONE
        res = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": activity.city})
        data = res.json()
        tz = data["results"][0]["timezone"]

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": activity.location.lat,                  # LATITUDE OF THE LOCATION OF EVENT
            "longitude": activity.location.lng,                 # LONGITUDE OF THE LOCATION OF EVENT
            "hourly": "weathercode",                            # STANDARD TEMPERATURE ANALYSIS ALTITUDE
            "start_date": start_dt.strftime("%Y-%m-%d"),        # STARTING DATE OF EVENT
            "end_date": end_dt.strftime("%Y-%m-%d"),            # ENDING DATE OF EVENT
            "timezone": tz                                      # TIMEZONE
        }

        response = requests.get(url, params=params)
        data = response.json()
        times = pd.to_datetime(data["hourly"]["time"])
        weather_codes = data["hourly"]["weathercode"]

        event_mask = (times >= start_dt) & (times <= end_dt)
        event_weather_codes = [weather_codes[i] for i, m in enumerate(event_mask) if m]
        event_weather = [WEATHER_CODE_MAP[code] for code in event_weather_codes]
        bad_weather = any(w in activity.weather_blockers for w in event_weather)
        return not bad_weather  # RETURN TRUE IF ALL WEATHER IS FINE
    except KeyError:
        return False


def fits_in_window(activity: Activity, client: Client, start_min: int) -> bool:
    """
    Checks if the currently-planned event fits in the client's day-planning window.
    Returns true if both the event start and end are within the client's day-plan window, false otherwise.
    """
    client_start_m, client_end_m = client.day_start_min, client.day_end_min
    dur_h, dur_m = (activity.duration_min // 60) % 24, (activity.duration_min % 60)

    e_start_m = start_min
    e_end_m = _time_to_minutes(time(dur_h, dur_m)) + start_min

    if e_end_m < e_start_m:
        e_end_m += (24 * 60)
    fits = (client_start_m <= e_start_m < client_end_m) and (client_start_m < e_end_m <= client_end_m)
    return fits


def make_day_plan(client: Client, activities: List[Activity], day: date) -> PlanDay:
    plan = PlanDay(day)

    # higher interest, then popularity
    acts_sorted = sorted(
        activities,
        key=lambda a: (interest_score_age(client, a), a.popularity),
        reverse=True,
    )

    for act in acts_sorted:
        step = choose_step_minutes(act) or 60
        for start_dt in generate_candidate_times(act, day, step_minutes=step):
            # Checks if the age restriction and start time is feasible based on 
            # when client starts and the duration of the activity with respect to its closing time
            hard_check = hard_feasible(client, act, start_dt)
            no_overlap = fits_no_overlap(plan.events, start_dt, act)
            window_fits = fits_in_window(act, client, client.day_start_min)

            if no_overlap and hard_check and window_fits:
                if is_weather_suitable(act, start_dt): # ONLY RUNS WEATHER CHECKS IF THE EVENT CAN FIT (OPTIMIZATION)
                    plan.add(PlanEvent(act, start_dt))
                    break

            placed = repairB(plan, client, act, day, start_dt, max_moves=1, try_others=True)
                
            if placed:
                break # E placed; move to next activity
            # else: try next candidate time for this act
    plan.events.sort(key=lambda e: e.start_dt)
    return plan


# ─────────────────────────────────────────────────────────────────────────────
# Repair helpers
# ─────────────────────────────────────────────────────────────────────────────

def _blocking_events(events: List[PlanEvent],
                     start_dt: datetime,
                     act: Activity) -> List[PlanEvent]:
    """Events that overlap if `act` starts at `start_dt`."""
    end_dt = start_dt + timedelta(minutes=act.duration_min)
    out = []
    for ev in events:
        if overlaps(start_dt, end_dt, ev.start_dt, ev.end_dt):
            out.append(ev)
    return out

def _overlap_minutes(start_dt: datetime,
                     act: Activity,
                     ev: PlanEvent) -> int:
    """How many minutes ev overlaps with E=[start_dt, start_dt+dur)."""
    a1 = start_dt
    a2 = start_dt + timedelta(minutes=act.duration_min)
    b1, b2 = ev.start_dt, ev.end_dt
    if a2 <= b1 or b2 <= a1:
        return 0
    inter_start = max(a1, b1)
    inter_end   = min(a2, b2)
    return int((inter_end - inter_start).total_seconds() // 60)


def _future_candidates(activity: Activity,
                       day: date,
                       after_dt: datetime) -> List[datetime]:
    """Feasible future starts for this activity strictly after `after_dt`."""
    step = choose_step_minutes(activity) or 60
    cands = generate_candidate_times(activity, day, step_minutes=step)
    return [t for t in cands if t > after_dt]


def _can_place_against(events: List[PlanEvent],
                       client: Client,
                       act: Activity,
                       when: datetime) -> bool:
    """Hard checks + no-overlap against `events`."""
    return hard_feasible(client, act, when) and fits_no_overlap(events, when, act) and is_weather_suitable(act, when)


def _time_to_minutes(dt):
    """
    Converts the time into actual minutes.
    """
    return dt.hour * 60 + dt.minute


def _try_nudge_forward(plan: PlanDay,
                       client: Client,
                       ev: PlanEvent,
                       day: date,
                       target_act: Activity,
                       target_start: datetime,
                       max_moves: int) -> bool:
    """
    Try moving `ev` forward by up to `max_moves` later candidate starts.
    If a move makes space, place (target_act @ target_start) and return True.
    Reverts the move if it didn't help.
    """
    if ev.activity.fixed_times:  # anchors don't move
        return False

    others = [x for x in plan.events if x is not ev]
    old_start, old_end = ev.start_dt, ev.end_dt

    tried = 0
    for t2 in _future_candidates(ev.activity, day, after_dt=ev.start_dt):
        if tried >= max_moves:
            break

        if _can_place_against(others, client, ev.activity, t2):
            # tentatively move the blocker
            ev.start_dt = t2
            ev.end_dt   = t2 + timedelta(minutes=ev.activity.duration_min)

            # did that free the slot for E?
            if _can_place_against(plan.events, client, target_act, target_start):
                plan.add(PlanEvent(target_act, target_start))
                return True

            # revert and try next t2
            ev.start_dt, ev.end_dt = old_start, old_end

        tried += 1

    return False


def _flexibility_now(plan: PlanDay,
                     client: Client,
                     ev: PlanEvent,
                     day: date) -> int:
    """
    Approx count of alternative feasible starts (forward only) available
    to `ev` right now (excluding fixed-times).
    """
    if ev.activity.fixed_times:
        return 0
    others = [x for x in plan.events if x is not ev]
    count = 0
    for t2 in _future_candidates(ev.activity, day, after_dt=ev.start_dt):
        if _can_place_against(others, client, ev.activity, t2):
            count += 1
    return count


# ─────────────────────────────────────────────────────────────────────────────
# Repair B: direct-conflict first, then try other planned events
# ─────────────────────────────────────────────────────────────────────────────

def repairB(plan: PlanDay,
            client: Client,
            act: Activity,
            day: date,
            start_dt: datetime,
            max_moves: int = 1,
            try_others: bool = True) -> bool:
    """
    Try to place `act` at `start_dt` by minimally adjusting existing events.

    1) Identify the event that most directly conflicts (max overlap minutes)
       and try nudging it forward up to `max_moves` later feasible starts.
    2) If that fails and `try_others` is True, try nudging other non-fixed events,
       ordered by least flexibility first (each by up to `max_moves` moves).
    Returns True iff `act` was placed.
    """
    # who blocks E right now?
    conflicts = _blocking_events(plan.events, start_dt, act)
    if not conflicts:
        # defensive: if caller mis-signaled, just place E
        plan.add(PlanEvent(act, start_dt))
        return True

    # 1) Direct conflicting event: the one with max overlap
    direct = max(conflicts, key=lambda ev: _overlap_minutes(start_dt, act, ev))
    if _try_nudge_forward(plan, client, direct, day, act, start_dt, max_moves=max_moves):
        return True

    # 2) Optionally try other planned events (non-fixed), least flexibility first
    if try_others:
        candidates = [ev for ev in plan.events if (ev is not direct and not ev.activity.fixed_times)]
        candidates.sort(key=lambda ev: _flexibility_now(plan, client, ev, day))

        for ev in candidates:
            if _try_nudge_forward(plan, client, ev, day, act, start_dt, max_moves=max_moves):
                return True

    return False


if __name__ == "__main__":
    # Force the test day to the concert day
    from datetime import date, datetime, time
    from planner.core.utils import load_people, load_events

    client = load_people()[0]
    events = load_events()

    event_data = {
        "id": "e_themepark_extreme_01",
        "name": "Thrill Seeker’s Mega Theme Park",
        "category": "theme_parks",
        "tags": ["theme_parks", "roller_coasters", "extreme", "outdoor"],
        "venue": "Wonderland",
        "city": "Toronto",
        "location": {"lat": 43.6426, "lng": -79.3860},
        "duration_min": 180,
        "cost_cad": 80,
        "age_min": 5,
        "age_max": 99,
        "opening_hours": {},
        "fixed_times": [{"date": "2026-08-02", "start": "10:00"}],
        "requires_booking": True,
        "weather_blockers": [],
        "popularity": 0.9
    }

    activity = Activity(**event_data)

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
    mock_rain_activity = Activity(**mock_rain_event)
    mock_location = Location(mock_rain_event["location"]["lat"], mock_rain_event["location"]["lng"], mock_rain_event["city"])
    mock_rain_activity.location = mock_location
    subset.append(mock_rain_activity)

    # Filter events based on weather for the greedy algorithm (optional test)
    filtered_subset = [e for e in subset if current_weather not in getattr(e, "weather_blockers", [])]

    print("Subset BEFORE weather filter:")
    for e in subset:
        print(f"- {e.name} (weather blockers: {e.weather_blockers})")

    print("\nSubset AFTER weather filter:")
    for e in filtered_subset:
        print(f"- {e.name}")

    plan = make_day_plan(client, subset, day)

    print(f"\nPlan for {day}:")
    for ev in plan.events:
        print(f"- {ev.start_dt.time()}–{ev.end_dt.time()}  {ev.activity.name} ({ev.activity.category})  ${ev.activity.cost_cad}")
