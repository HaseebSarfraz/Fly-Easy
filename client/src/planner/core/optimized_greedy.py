from __future__ import annotations
# src/planner/core/solver.py

tz_cache = {}
weather_cache = {}

# src/planner/core/optimized_greedy
from datetime import date, datetime, timedelta
from typing import List
from planner.core.models import Client, Activity, PlanDay, PlanEvent, Location
from planner.core.constraints import hard_feasible, hc_open_window_ok, hc_age_ok
from planner.core.timegrid import generate_candidate_times, choose_step_minutes
from planner.core.scoring import interest_score
from planner.core.utils import to_minutes
from planner.core.scoring import base_value
from .utils import place_to_activity
from .food_filter import cuisine_query, violates_avoid
from .places import fetch_nearby_food
from math import cos, radians
from planner.core.scoring import interest_score, duration_penalty, conflict_penalty
from typing import Optional
import re
from heapq import heappush, heappop
from dataclasses import dataclass


import requests
import pandas as pd
added_activities = {}

@dataclass
class PlannerConfig:
    # Hard constraints (age, opening hours, etc. via hard_feasible)
    use_hard_constraints: bool = True

    # Weather constraints (Open-Meteo + blockers list)
    use_weather: bool = True

    # Daily budget soft cap + over-budget penalty
    use_budget: bool = True

    # Pre-add meals (restaurant advisor)
    use_meals: bool = True

    # Use Yash beam-search base-plan as “primary_acts”
    use_base_plan: bool = True

    # Allow RepairB to nudge events and make room
    use_repairB: bool = True

    # Debug prints inside make_day_plan (anchors, etc)
    debug_print: bool = True

def _dbg(cfg: PlannerConfig, *args, **kwargs):
    """Conditional debug printing."""
    if cfg.debug_print:
        print(*args, **kwargs)


RADIUS_STEPS = [1500, 3000, 4000]  # meters

_DASHES = {"–","—","−"}

tz_cache = {}
weather_cache = {}


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

LAMBDA_BUDGET = 0.03      # penalty $→points (e.g., 0.03 pts per $1 over)
SCORE_THRESHOLD = 0.10    # minimum net score to accept when over budget

WEATHER_CACHE: dict[tuple, tuple] = {}  # (lat3,lng3,day_iso,tz) -> (pd.DatetimeIndex, list[int])

def _bump_tags(tags_encountered: dict[str, int], act: Activity) -> None:
    """Increment tag counts for this activity in the given dict."""
    for tag in getattr(act, "tags", []) or []:
        tags_encountered[tag] = tags_encountered.get(tag, 0) + 1

def _cache_key(lat: float, lng: float, day_iso: str, tz: str):
    # round to collapse tiny lat/lng differences at city scale
    return (round(float(lat), 3), round(float(lng), 3), day_iso, tz)

def _fetch_hourly_once(lat: float, lng: float, day_iso: str, tz: str):
    """Fetch hourly weathercode for a single date; cached."""
    key = _cache_key(lat, lng, day_iso, tz)
    if key in WEATHER_CACHE:
        return WEATHER_CACHE[key]

    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lng,
            "hourly": "weathercode",
            "start_date": day_iso,
            "end_date": day_iso,  # same day
            "timezone": tz,
        },
        timeout=2.0,
    )
    r.raise_for_status()
    j = r.json()
    hourly = j.get("hourly") or {}
    times = pd.to_datetime(hourly.get("time", []), errors="coerce")
    codes = hourly.get("weathercode", []) or []
    WEATHER_CACHE[key] = (times, codes)
    return WEATHER_CACHE[key]

def _days_in_trip(client: Client) -> int:
    # Guard against 0
    return max(1, (client.trip_end - client.trip_start).days + 1)

def _soft_cap_per_day(client: Client) -> float:
    return float(client.budget_total) / _days_in_trip(client)

def _spent_today(plan: PlanDay) -> float:
    return float(sum(ev.activity.cost_cad for ev in plan.events))

def _net_score_with_budget(client, act, plan, soft_cap_day, already_added=False):
    base = base_value(client, act)
    spent = _spent_today(plan) + (0.0 if already_added else float(act.cost_cad))
    over  = max(0.0, spent - soft_cap_day)
    penalty = LAMBDA_BUDGET * over
    return base - penalty

def overlaps(a_start, a_end, b_start, b_end) -> bool:
    return not (a_end <= b_start or b_end <= a_start)


def fits_no_overlap(events: List[PlanEvent], start_dt: datetime, act: Activity) -> bool:
    end_dt = start_dt + timedelta(minutes=act.duration_min)
    for ev in events:
        if overlaps(start_dt, end_dt, ev.start_dt, ev.end_dt):
            return False
    return True


def get_timezone(city: str) -> str:
    if city in tz_cache:
        return tz_cache[city]

    res = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city})
    data = res.json()
    tz = data["results"][0]["timezone"]
    tz_cache[city] = tz
    return tz


_TZ_CACHE: dict[str, str] = {}

def is_weather_suitable(activity: Activity, start_dt: datetime) -> bool:
    blockers = getattr(activity, "weather_blockers", None) or []
    if not blockers:
        return True

    # guard event window
    dur_min = int(getattr(activity, "duration_min", 0) or 60)
    end_dt = start_dt + timedelta(minutes=dur_min)

    try:
        city = getattr(activity, "city", "") or ""
        tz = _TZ_CACHE.get(city)
        if not tz:
            gres = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city},
                timeout=2.0,
            )
            gres.raise_for_status()
            gj = gres.json()
            if not gj or "results" not in gj or not gj["results"]:
                return True
            tz = gj["results"][0].get("timezone")
            if not tz:
                return True
            _TZ_CACHE[city] = tz
    except Exception as e:
        print(f"[weather] Geocoding failed: {e}")
        return True

    try:
        day1 = start_dt.strftime("%Y-%m-%d")
        times1, codes1 = _fetch_hourly_once(activity.location.lat, activity.location.lng, day1, tz)

        times_all, codes_all = list(times1), list(codes1)
        if end_dt.date() != start_dt.date():
            day2 = end_dt.strftime("%Y-%m-%d")
            t2, c2 = _fetch_hourly_once(activity.location.lat, activity.location.lng, day2, tz)
            times_all += list(t2)
            codes_all += list(c2)

        if not times_all or len(times_all) != len(codes_all):
            print("[weather] times/codes missing or mismatched; fail-open")
            return True


        s = pd.Timestamp(start_dt)
        e = pd.Timestamp(end_dt)
        event_names = []
        for t, code in zip(times_all, codes_all):
            if pd.isna(t):
                continue
            if s <= t <= e:
                event_names.append(WEATHER_CODE_MAP.get(int(code), str(code)))

        if not event_names:
            return True

        return not any(name in blockers for name in event_names)

    except Exception as e:
        print(f"[weather] Forecast failed: {e}; fail-open")
        return True



def _to_minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def _from_minutes(day, minutes_from_midnight):
    h = minutes_from_midnight // 60
    m = minutes_from_midnight % 60
    return datetime(day.year, day.month, day.day, h, m)

# ─────────────────────────────────────────────────────────────────────────────
# Restaurant advisor 
# ─────────────────────────────────────────────────────────────────────────────
def _window_midpoint(start_hhmm, end_hhmm, duration_min=60, buffer_min=10):
    """
    Choose a human-ish start time for a meal inside [start,end],
    centered near the midpoint, padded by a small buffer on both ends.
    """
    s = _to_minutes(start_hhmm) + buffer_min
    e = _to_minutes(end_hhmm) - buffer_min
    if e - s < duration_min:
        # If the declared window is too small, just start at s (best effort)
        return s
    mid = (s + e - duration_min) // 2
    return max(s, min(mid, e - duration_min))

def _dist_m(lat1, lng1, lat2, lng2):
    k = 111_320.0
    dx = (lng2 - lng1) * k * cos(radians(lat1))
    dy = (lat2 - lat1) * k
    return (dx*dx + dy*dy) ** 0.5

def _google_places_candidates(center_loc, cuisine_query_str: Optional[str]):
    """Return (status, results_list). Keeps status for debugging."""
    # try 1: cuisine-biased search (TextSearch)
    if cuisine_query_str:
        for r in RADIUS_STEPS:
            data = fetch_nearby_food(center_loc.lat, center_loc.lng, radius_m=r, query=cuisine_query_str)
            if data.get("results"):
                return data.get("status","OK"), data["results"]
    # try 2: any restaurant (Nearby)
    for r in RADIUS_STEPS:
        data = fetch_nearby_food(center_loc.lat, center_loc.lng, radius_m=r, query=None)
        if data.get("results"):
            return data.get("status","OK"), data["results"]
    return data.get("status","ZERO_RESULTS"), []


def _positive_keywords_ok(place, positives):
    """Optional: enforce halal/kosher/vegan/gluten-free etc. if provided."""
    if not positives:
        return True
    text = " ".join([
        place.get("name",""),
        place.get("vicinity",""),
        " ".join(place.get("types", []))
    ]).lower()
    return all(p.lower() in text for p in positives)


def _best_restaurant_for_window(center_loc, city, likes, avoid_terms, required_terms=None):
    """
    Expand over cuisines and radius. If nothing with cuisines, fall back to any restaurant.
    Apply negative + positive filters. Rank and pick best.
    """
    # Build cuisine text query from all likes (do separate passes rather than one mega-string)
    # Pass 1: try each cuisine individually (tends to be higher quality than one giant OR)
    liked_queries = likes or []
    tried_statuses = []

    def _rank_key(p):
        rating = float(p.get("rating", 0.0))
        reviews = int(p.get("user_ratings_total", p.get("user_ratings", 0)) or 0)
        loc = (p.get("geometry") or {}).get("location") or {}
        plat, plng = float(loc.get("lat", center_loc.lat)), float(loc.get("lng", center_loc.lng))
        dist = _dist_m(center_loc.lat, center_loc.lng, plat, plng)
        return (rating, reviews, -dist)

    # Try each cuisine on its own
    for q in liked_queries:
        status, results = _google_places_candidates(center_loc, q)
        tried_statuses.append(("q:"+q, status, len(results)))
        filtered = [p for p in results if not violates_avoid(p, avoid_terms)]
        if required_terms:
            filtered = [p for p in filtered if _positive_keywords_ok(p, required_terms)]
        if filtered:
            return max(filtered, key=_rank_key)

    # Try all cuisines together (sometimes this catches multi-tag places)
    if liked_queries:
        status, results = _google_places_candidates(center_loc, " ".join(liked_queries))
        tried_statuses.append(("q:ALL", status, len(results)))
        filtered = [p for p in results if not violates_avoid(p, avoid_terms)]
        if required_terms:
            filtered = [p for p in filtered if _positive_keywords_ok(p, required_terms)]
        if filtered:
            return max(filtered, key=_rank_key)

    # Fallback: any restaurant nearby
    status, results = _google_places_candidates(center_loc, None)
    tried_statuses.append(("q:any", status, len(results)))
    filtered = [p for p in results if not violates_avoid(p, avoid_terms)]
    if required_terms:
        filtered = [p for p in filtered if _positive_keywords_ok(p, required_terms)]
    if filtered:
        return max(filtered, key=_rank_key)

    # Last resort: We coudln't find any restauntants near by. 
    print("[places] no candidates:", tried_statuses)
    return None

def _meal_window(client: Client, meal: str) -> tuple[str, str]:
    """
    Supports either:
      client.meal_prefs[meal]["window"] = ["09:30","11:00"]
    or
      client.meal_windows[meal] = {"start":"09:30","end":"11:00"}
    """
    # preferred new schema
    if hasattr(client, "meal_prefs") and client.meal_prefs and meal in client.meal_prefs:
        win = client.meal_prefs[meal].get("window")
        if isinstance(win, (list, tuple)) and len(win) == 2:
            return win[0], win[1]

    # legacy schema
    if hasattr(client, "meal_windows") and client.meal_windows and meal in client.meal_windows:
        w = client.meal_windows[meal]
        return w["start"], w["end"]

    raise KeyError(f"Meal window missing for '{meal}'")

def _meal_cuisines(client: Client, meal: str) -> list[str]:
    """
    Returns cuisine likes for a given meal if present; else [].
    Expects client.meal_prefs[meal]["cuisines"] under your new schema.
    """
    if hasattr(client, "meal_prefs") and client.meal_prefs and meal in client.meal_prefs:
        return client.meal_prefs[meal].get("cuisines", []) or []
    return []

def _derive_diet_terms(diet: dict) -> tuple[list[str], list[str]]:
    """
    Convert booleans into positive requirements and avoid lists.
    Example input (current schema):
      {"vegetarian": False, "vegan": False, "halal": True, "kosher": False,
       "gluten_free": False, "dairy_free": False, "nut_allergy": True,
       "avoid": ["pork"], "required_terms": []}
    """
    req = list(diet.get("required_terms", []))  # allow explicit overrides
    avoid = list(diet.get("avoid", []))

    # Positive requirements (if True => require)
    if diet.get("halal"):        req.append("halal")
    if diet.get("kosher"):       req.append("kosher")
    if diet.get("vegan"):        req.append("vegan")
    if diet.get("vegetarian"):   req.append("vegetarian")
    if diet.get("gluten_free"):  req.extend(["gluten free", "gluten-free"])
    if diet.get("dairy_free"):   req.extend(["dairy free", "dairy-free"])

    # Allergies -> avoid terms
    if diet.get("nut_allergy"):
        avoid.extend(["peanut", "peanuts", "almond", "walnut", "cashew", "tree nut", "nuts"])

    # Dedup + normalize
    req   = sorted({t.lower() for t in req})
    avoid = sorted({t.lower() for t in avoid})
    return req, avoid

def _dist_m(lat1, lng1, lat2, lng2):
    k = 111_320.0
    dx = (lng2 - lng1) * k * cos(radians(lat1))
    dy = (lat2 - lat1) * k
    return (dx*dx + dy*dy) ** 0.5

def _travel_buffer_min(a_act: Activity, b_act: Activity) -> int:
    """Very light travel estimate for padding between events."""
    d_m = _dist_m(a_act.location.lat, a_act.location.lng, b_act.location.lat, b_act.location.lng)
    # ~12 min/km walk, clamp [5, 35]
    return max(5, min(int((d_m/1000.0)*12), 35))

def _overlaps_ev(a_start, a_dur_min, b_start, b_dur_min) -> bool:
    a_end = a_start + timedelta(minutes=a_dur_min)
    b_end = b_start + timedelta(minutes=b_dur_min)
    return not (a_end <= b_start or b_end <= a_start)

def reconcile_meals_with_anchors(plan: PlanDay) -> None:
    """If a meal overlaps a fixed event, prefer moving meal before, else after,
    else shorten, else convert to grab-and-go. Adds small travel buffers."""
    meals = [ev for ev in plan.events if ev.activity.category == "food"]
    anchors = [ev for ev in plan.events if ev.activity.fixed_times]

    if not meals or not anchors:
        return

    # Work per anchor; if multiple anchors exist, this still behaves locally well
    for anchor in anchors:
        for meal in meals:
            if not _overlaps_ev(meal.start_dt, meal.activity.duration_min, anchor.start_dt, anchor.activity.duration_min):
                continue

            buf = _travel_buffer_min(meal.activity, anchor.activity)
            new_end = anchor.start_dt - timedelta(minutes=buf)
            new_start = new_end - timedelta(minutes=meal.activity.duration_min)
            if new_start.date() == meal.start_dt.date() and new_start < new_end:
                # also avoid colliding with anything else
                if fits_no_overlap([e for e in plan.events if e is not meal and e is not anchor], new_start, meal.activity):
                    meal.start_dt = new_start
                    meal.end_dt   = new_end
                    meal.activity.tags.append("note:eat before fixed event")
                    continue

            buf2 = _travel_buffer_min(anchor.activity, meal.activity)
            new_start2 = anchor.end_dt + timedelta(minutes=buf2)
            if fits_no_overlap([e for e in plan.events if e is not meal and e is not anchor], new_start2, meal.activity):
                meal.start_dt = new_start2
                meal.end_dt   = new_start2 + timedelta(minutes=meal.activity.duration_min)
                meal.activity.tags.append("note:eat after fixed event")
                continue

            quick_min = max(30, min(45, meal.activity.duration_min))  # 30–45min quick meal
            new_end3 = anchor.start_dt - timedelta(minutes=buf)
            new_start3 = new_end3 - timedelta(minutes=quick_min)
            if new_start3 < new_end3 and fits_no_overlap([e for e in plan.events if e is not meal and e is not anchor], new_start3, meal.activity):
                meal.activity.duration_min = quick_min
                meal.start_dt = new_start3
                meal.end_dt   = new_end3
                meal.activity.tags.append("note:shortened quick meal")
                continue

            snack_min = 15
            new_end4 = anchor.start_dt - timedelta(minutes=buf)
            new_start4 = new_end4 - timedelta(minutes=snack_min)
            meal.activity.name = f"{meal.activity.name} (grab-and-go)"
            meal.activity.duration_min = snack_min
            meal.activity.tags += ["note:grab-and-go", "note:anchor overlap"]
            meal.start_dt = new_start4
            meal.end_dt   = new_end4


def _overlaps_ev(a_start, a_dur_min, b_start, b_dur_min) -> bool:
    a_end = a_start + timedelta(minutes=a_dur_min)
    b_end = b_start + timedelta(minutes=b_dur_min)
    return not (a_end <= b_start or b_end <= a_start)

def _dist_m(lat1, lng1, lat2, lng2):
    # quick planar distance (meters)
    from math import cos, radians
    k = 111_320.0
    dx = (lng2 - lng1) * k * cos(radians(lat1))
    dy = (lat2 - lat1) * k
    return (dx*dx + dy*dy) ** 0.5

def _travel_buffer_min(a_act, b_act) -> int:
    d_m = _dist_m(a_act.location.lat, a_act.location.lng,
                  b_act.location.lat, b_act.location.lng)
    return max(5, min(int((d_m/1000.0)*12), 35))  # ~12 min/km, clamp [5,35]

def _resolve_meal_conflict(plan, client, meal_ev, anchor_ev) -> bool:
    """
    Try to keep the meal if it overlaps with a fixed-time anchor:
      1) move meal before show with travel buffer
      2) else move after show with buffer
      3) else shorten meal (30–45m) before show
      4) else convert to 15m grab-and-go before show
    Returns True iff conflict resolved (meal kept in some form).
    """
    # no-op if no overlap
    if not _overlaps_ev(meal_ev.start_dt, meal_ev.activity.duration_min,
                        anchor_ev.start_dt, anchor_ev.activity.duration_min):
        return True

    others = [e for e in plan.events if e is not meal_ev and e is not anchor_ev]


    buf = _travel_buffer_min(meal_ev.activity, anchor_ev.activity)
    new_end = anchor_ev.start_dt - timedelta(minutes=buf)
    new_start = new_end - timedelta(minutes=meal_ev.activity.duration_min)
    if new_start < new_end and fits_no_overlap(others, new_start, meal_ev.activity):
        meal_ev.start_dt, meal_ev.end_dt = new_start, new_end
        meal_ev.activity.tags.append("note:eat before event")
        return True


    buf2 = _travel_buffer_min(anchor_ev.activity, meal_ev.activity)
    new_start2 = anchor_ev.end_dt + timedelta(minutes=buf2)
    if fits_no_overlap(others, new_start2, meal_ev.activity):
        meal_ev.start_dt = new_start2
        meal_ev.end_dt = new_start2 + timedelta(minutes=meal_ev.activity.duration_min)
        meal_ev.activity.tags.append("note:eat after event")
        return True

    quick_min = max(30, min(45, meal_ev.activity.duration_min))
    new_end3 = anchor_ev.start_dt - timedelta(minutes=buf)
    new_start3 = new_end3 - timedelta(minutes=quick_min)
    if new_start3 < new_end3 and fits_no_overlap(others, new_start3, meal_ev.activity):
        meal_ev.activity.duration_min = quick_min
        meal_ev.start_dt, meal_ev.end_dt = new_start3, new_end3
        meal_ev.activity.tags.append("note:shortened quick meal")
        return True

    snack_min = 15
    new_end4 = anchor_ev.start_dt - timedelta(minutes=buf)
    new_start4 = new_end4 - timedelta(minutes=snack_min)
    meal_ev.activity.name = f"{meal_ev.activity.name} (grab-and-go)"
    meal_ev.activity.duration_min = snack_min
    meal_ev.activity.tags += ["note:grab-and-go", "note:anchor overlap"]
    meal_ev.start_dt, meal_ev.end_dt = new_start4, new_end4
    return True


def pre_add_rests(plan, client, day, center_loc=None, default_duration_min=60):
    center = center_loc or client.home_base

    # derive avoid/required terms below (see Issue #2)
    req_terms, avoid_terms = _derive_diet_terms(client.dietary or {})

    for meal in ["breakfast", "lunch", "dinner"]:
        s, e = _meal_window(client, meal)
        start_minute = _window_midpoint(s, e, duration_min=default_duration_min, buffer_min=10)
        start_dt = _from_minutes(day, start_minute)

        likes = _meal_cuisines(client, meal)
        place = _best_restaurant_for_window(center, center.city, likes, avoid_terms=avoid_terms, required_terms=req_terms)

        if place:
            meal_act = place_to_activity(place, center.city, default_duration_min, 0.0)
        else:
            meal_act = Activity(
                id=f"meal_{meal}_{day.isoformat()}",
                name=f"{meal.capitalize()} (nearby options)",
                category="food",
                tags=["food","restaurant"],
                venue=center.city,
                city=center.city,
                location=center,
                duration_min=default_duration_min,
                cost_cad=0.0,
                age_min=0, age_max=99,
                opening_hours={"daily":["06:00","23:00"]},
                fixed_times=[],
                requires_booking=False,
                weather_blockers=[],
                popularity=0.0,
                vibe_tags=[],
            )
        plan.add(PlanEvent(meal_act, start_dt))

def _fixed_dt_candidates(act: Activity, day: date) -> list[datetime]:
    """Turn act.fixed_times (like ['17:00']) into datetime starts on `day`."""
    out = []
    fts = getattr(act, "fixed_times", []) or []
    for ft in fts:
        # accept 'HH:MM' or 'HH:MM–HH:MM' (use the first time)
        s = ft
        if isinstance(ft, str) and " " not in ft and "-" in ft:
            s = ft.split("-")[0].strip()
        if isinstance(s, str) and ":" in s:
            hh, mm = s.split(":")
            try:
                out.append(datetime(day.year, day.month, day.day, int(hh), int(mm)))
            except ValueError:
                pass
    return out

def _has_fixed_times(a: Activity) -> bool:
    ft = getattr(a, "fixed_times", None)
    # treat any non-empty list/str/dict as "has fixed times"
    if isinstance(ft, list):
        return len(ft) > 0
    if isinstance(ft, (str, dict)):
        return bool(ft)
    return False


def _normalize_time_str(s: str) -> str:
    s = s.strip()
    for d in _DASHES:
        s = s.replace(d, "-")
    return s

def _parse_one_time(s: str, day: date) -> datetime | None:
    s = s.strip()
    if re.match(r"^\d{1,2}:\d{2}$", s):
        hh, mm = s.split(":")
        try:
            return datetime(day.year, day.month, day.day, int(hh), int(mm))
        except ValueError:
            return None
    for fmt in ("%I:%M %p", "%I %p", "%I%p"):
        try:
            t = datetime.strptime(s.upper(), fmt).time()
            return datetime(day.year, day.month, day.day, t.hour, t.minute)
        except ValueError:
            pass
    return None

def _fixed_dt_candidates(act: Activity, day: date) -> list[datetime]:
    fts = getattr(act, "fixed_times", []) or []
    # normalize to list
    if isinstance(fts, (str, dict)):
        fts = [fts]

    out: list[datetime] = []
    for raw in fts:
        # case 1: dict schema like {'date':'YYYY-MM-DD','start':'17:00'} (your concert)
        if isinstance(raw, dict):
            dstr = raw.get("date")
            tstr = raw.get("start") or raw.get("time") or raw.get("start_time")
            # if a date is given and doesn't match this day, skip
            if dstr and dstr != day.isoformat():
                continue
            if tstr:
                dt = _parse_one_time(tstr, day)
                if dt:
                    out.append(dt)
            continue

        # case 2: string "HH:MM" or "HH:MM-HH:MM" or "YYYY-MM-DD HH:MM"
        if isinstance(raw, str):
            s = _normalize_time_str(raw)
            # optional "YYYY-MM-DD HH:MM"
            if " " in s and re.match(r"^\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}$", s):
                dpart, tpart = s.split(None, 1)
                if dpart == day.isoformat():
                    dt = _parse_one_time(tpart, day)
                    if dt:
                        out.append(dt)
                continue
            # "HH:MM" or "HH:MM-HH:MM" -> take the left side
            start_part = s.split("-", 1)[0].strip()
            dt = _parse_one_time(start_part, day)
            if dt:
                out.append(dt)
            continue
        # ignore anything else silently

    return out

def _hard_feasible_for_anchor(
    client: Client,
    act: Activity,
    start_dt: datetime,
    cfg: Optional[PlannerConfig] = None,
) -> bool:
    cfg = cfg or PlannerConfig()

    # Age / other “hard” checks
    if cfg.use_hard_constraints and not hc_age_ok(client, act):
        return False

    # Weather (Open-Meteo + blockers list)
    if cfg.use_weather and not is_weather_suitable(act, start_dt):
        return False

    return True




def fits_in_window(activity: Activity, client: Client, start_min: int) -> bool:
    """
    Checks if the currently-planned event fits in the client's day-planning window.
    Returns true if both the event start and end are within the client's day-plan window, false otherwise.
    """
    client_start_m, client_end_m = client.day_start_min, client.day_end_min

    e_start_m = start_min
    e_end_m = activity.duration_min + start_min

    if e_end_m < e_start_m:
        e_end_m += (24 * 60)
    fits = (client_start_m <= e_start_m < client_end_m) and (client_start_m < e_end_m <= client_end_m)
    return fits


def _allocate_time_by_interest(act, interest_scores, beta=1.3) -> dict:
    """
    Yash helper: compute per-member time allocation for an activity
    proportional to interest_scores.
    (We only use this indirectly via _build_base_plan for now.)
    """
    duration = act.duration_min
    if not interest_scores:
        return {}

    max_interest = max(interest_scores.values())
    most_interested = [m for m, s in interest_scores.items()
                       if s == max_interest][0]

    # Exponential weighting: higher interest ⇒ more time
    fair_pen_factors = {
        m: (score / 10) ** beta
        for m, score in interest_scores.items()
        if score > 0
    }
    total_weight = float(sum(fair_pen_factors.values())) or 1.0

    member_time_allocation = {
        m: duration * (w / total_weight)
        for m, w in fair_pen_factors.items()
    }

    # If some members had 0 interest, give any leftover time to the most interested
    allocated = sum(member_time_allocation.values())
    leftover = duration - allocated
    if leftover > 0:
        member_time_allocation[most_interested] = \
            member_time_allocation.get(most_interested, 0) + leftover

    return member_time_allocation


def _build_base_plan(client: Client,
                     activities: List[Activity],
                     threshold: float = 0.75,
                     beam: int = 8) -> list[list[Activity]]:
    """
    Yash helper: build several "base plans" that maximize group satisfaction.

    Returns a list of candidate activity lists.
    We'll take the first (best) one and try to schedule those activities first.
    """
    candidates: list[tuple[Activity, set, float]] = []

    for act in activities:
        interested = set()
        total_score = 0.0

        for person in getattr(client, "party_members", []):
            iw = sum(client.interest(tag, person) for tag in act.tags)
            if iw > 0:
                max_possible = 10 * max(1, len(act.tags))
                # per-activity threshold & sanity check w.r.t. day length
                if (
                    iw / max_possible >= threshold
                    and act.duration_min / max(1, client.total_day_duration)
                    <= getattr(client, "daily_act_time_per_member", 1.0)
                ):
                    interested.add(person)
                    total_score += iw

        if interested:
            candidates.append((act, interested, total_score))

    # Strong candidates first: more people + higher score
    candidates.sort(key=lambda x: (len(x[1]), x[2]), reverse=True)

    # Beam search over subsets of activities
    plans: list[tuple[list[Activity], set, float]] = [([], set(), 0.0)]
    # (chosen_acts, satisfied_people, score)

    for act, interested, score in candidates:
        new_plans: list[tuple[list[Activity], set, float]] = []

        for acts, sat, s in plans:
            # Option 1: skip act
            new_plans.append((acts, sat, s))

            # Option 2: include act if it adds at least one new satisfied person
            new_people = interested - sat
            if new_people:
                new_plans.append((
                    acts + [act],
                    sat | new_people,
                    s + score,
                ))

        # Keep only top `beam` partial plans
        new_plans.sort(
            key=lambda p: (len(p[1]), p[2]),  # more people, higher score
            reverse=True,
        )
        plans = new_plans[:beam]

    # Drop satisfaction metadata; return just activity lists
    return [p[0] for p in plans]


def make_multi_day_plan(client: Client, activities: list[Activity]) -> list[PlanDay]:
    """
    This function returns a list of plans, one for each day.
    """
    result = []
    current_day = client.trip_start

    # DICTIONARY TO STORE NUMBER OF SATISFACTIONS PER PERSON, USED FOR PRIORITIZATION OF ACTIVITIES.
    person_satisfaction = {
        person: 0
        for person in getattr(client, "partymembers", [])
    }

    for _ in client.trip_days:
        result.append(make_day_plan(client, activities, current_day, person_satisfaction))
        current_day += timedelta(1)
        client.credits_left = {c["name"]: client.cpm for c in client.party_members}
    added_activities.clear()    # ONCE DONE MAKING PLAN, RESET
    return result



def make_day_plan(
    client: Client,
    activities: List[Activity],
    day: date,
    config: Optional[PlannerConfig] = None,
) -> PlanDay:
    """
    Combined Haseeb + Yash logic with toggles via PlannerConfig.
    """
    cfg = config or PlannerConfig()

    # ─────────────────────────────────────────────────────────────────────
    # 1) Split into anchors vs flex
    # ─────────────────────────────────────────────────────────────────────
    anchors = [a for a in activities if _has_fixed_times(a)]
    flex    = [a for a in activities if not _has_fixed_times(a)]

    _dbg(cfg, "ANCHORS:", [
        (a.id, type(getattr(a, "fixed_times", None)).__name__,
         getattr(a, "fixed_times", None))
        for a in anchors
    ])

    # ─────────────────────────────────────────────────────────────────────
    # 2) Budget per day + reserved_cap for flex (Haseeb logic)
    # ─────────────────────────────────────────────────────────────────────
    anchor_cost = sum(float(a.cost_cad or 0.0) for a in anchors)
    if cfg.use_budget:
        soft_cap_day = _soft_cap_per_day(client)
        reserved_cap = max(0.0, soft_cap_day - anchor_cost)
    else:
        # Effectively "no budget" for scoring decisions
        soft_cap_day = float("inf")
        reserved_cap = float("inf")

    # ─────────────────────────────────────────────────────────────────────
    # 3) Start plan + pre-add meals
    # ─────────────────────────────────────────────────────────────────────
    plan = PlanDay(day)
    if cfg.use_meals:
        pre_add_rests(plan, client, day, center_loc=client.home_base)

    # ─────────────────────────────────────────────────────────────────────
    # 4) Place anchors first, reshaping meals around them
    # ─────────────────────────────────────────────────────────────────────
    for act in anchors:
        fixed_slots = _fixed_dt_candidates(act, day)
        candidate_starts = fixed_slots or list(
            generate_candidate_times(
                act, day,
                step_minutes=(choose_step_minutes(act) or 60)
            )
        )
        _dbg(cfg, f"[anchor] considering {act.id} at:", candidate_starts)

        placed = False
        for start_dt in candidate_starts:
            if not _hard_feasible_for_anchor(client, act, start_dt, cfg):
                _dbg(cfg, f"[anchor] {act.id} @ {start_dt.time()} hard-feasible=NO")
                continue

            # enforce a minimum duration so overlap math isn't degenerate
            if getattr(act, "duration_min", None) in (None, 0):
                act.duration_min = 120  # e.g., concerts default to 2h

            anchor_ev = PlanEvent(act, start_dt)
            plan.add(anchor_ev)
            _dbg(cfg, f"[anchor] added {act.id} @ {start_dt.time()} (dur {act.duration_min}m)")

            ok = True
            meals = [
                e for e in plan.events
                if e is not anchor_ev and e.activity.category == "food"
            ]
            for m in meals:
                if _overlaps_ev(
                    m.start_dt, m.activity.duration_min,
                    anchor_ev.start_dt, anchor_ev.activity.duration_min
                ):
                    moved = _resolve_meal_conflict(plan, client, m, anchor_ev)
                    _dbg(cfg, f"[anchor] meal conflict with {m.activity.name}: moved={moved}")
                    if not moved:
                        ok = False
                        break

            if ok:
                placed = True
                _dbg(cfg, f"[anchor] SUCCESS {act.id} placed @ {start_dt.time()}")
                break

            # rollback and try next start_dt
            plan.events.remove(anchor_ev)
            _dbg(cfg, f"[anchor] ROLLBACK {act.id} @ {start_dt.time()}")


    # ─────────────────────────────────────────────────────────────────────
    # 5) Track tag frequencies for conflict_penalty
    # ─────────────────────────────────────────────────────────────────────
    tags_encountered: dict[str, int] = {}
    for ev in plan.events:
        _bump_tags(tags_encountered, ev.activity)

    # ─────────────────────────────────────────────────────────────────────
    # 5) Use Yash's beam search to pick a good subset of flex activities
    # ─────────────────────────────────────────────────────────────────────
    if cfg.use_base_plan:
        base_plans = _build_base_plan(client, flex, threshold=0.75, beam=8)
        primary_acts: List[Activity] = base_plans[0] if base_plans else []
        primary_ids = {a.id for a in primary_acts}
        remaining_flex = [a for a in flex if a.id not in primary_ids]
    else:
        primary_acts = []
        remaining_flex = list(flex)

    # Sort remaining flex activities by Yash-style interest score, tie-breaking
    # with Haseeb's base_value (pure utility)
    def _interest_total(a: Activity) -> float:
        try:
            i_score, e_creds, ii_score = interest_score(client, a)
            if not ii_score:
                return 0.0
            avg_score = sum(ii_score.values()) / len(ii_score)

            dur_pen = duration_penalty(a, client, avg_score)
            conf_pen = conflict_penalty(a, client, tags_encountered)

            return max(i_score - dur_pen - conf_pen, 0.0)
        except Exception:
            return 0.0

    remaining_sorted = sorted(
        remaining_flex,
        key=lambda a: (_interest_total(a), base_value(client, a)),
        reverse=True,
    )

    # Final order to try scheduling flex activities:
    #   1) high-coverage base-plan activities
    #   2) other flex ordered by interest + base_value
    acts_sorted: List[Activity] = list(primary_acts) + remaining_sorted

    # ─────────────────────────────────────────────────────────────────────
    # 6) Greedy scheduling of flex activities (Haseeb's engine)
    # ─────────────────────────────────────────────────────────────────────
    for act in acts_sorted:
        step = choose_step_minutes(act) or 60
        added_activities.setdefault(act.id, False)
        if added_activities[act.id]:
            continue

        for start_dt in generate_candidate_times(act, day, step_minutes=step):
            # Basic hard constraints
            if cfg.use_hard_constraints and not hard_feasible(client, act, start_dt):
                continue
            if cfg.use_weather and not is_weather_suitable(activity=act, start_dt=start_dt):
                continue

            # Case A: fits without overlap
            if fits_no_overlap(plan.events, start_dt, act):
                # --- intrinsic utility using duration_penalty + conflict_penalty ---
                i_score, _, indiv_scores = interest_score(client, act)
                if indiv_scores:
                    avg_indiv = sum(indiv_scores.values()) / len(indiv_scores)
                else:
                    avg_indiv = i_score

                dur_pen = duration_penalty(act, client, avg_indiv)
                conf_pen = conflict_penalty(act, client, tags_encountered)
                intrinsic = max(i_score - dur_pen - conf_pen, 0.0)

                if cfg.use_budget:
                    projected_spent = _spent_today(plan) + float(act.cost_cad)
                    over = max(0.0, projected_spent - reserved_cap)
                    net = intrinsic - LAMBDA_BUDGET * over

                    if (over == 0.0) or (over > 0.0 and net >= SCORE_THRESHOLD):

                        plan.add(PlanEvent(act, start_dt))
                        added_activities[act.id] = True
                        _bump_tags(tags_encountered, act)  # record tags for this day
                        break
                    # not worth it at this start time → try next candidate
                    continue
                else:
                    # No budget logic: just require the intrinsic score to be decent
                    if intrinsic >= SCORE_THRESHOLD:
                        plan.add(PlanEvent(act, start_dt))
                        added_activities[act.id] = True
                        _bump_tags(tags_encountered, act)
                        break
                    # otherwise, reject this time and try the next start
                    continue

            # Case B: try to repair by nudging existing events (RepairB)
            if not cfg.use_repairB:
                # not allowed to nudge, just try next time slot
                continue

            snapshot = [(ev, ev.start_dt, ev.end_dt) for ev in plan.events]
            if repairB(plan, client, act, day, start_dt,
                       max_moves=1, try_others=True, config=cfg):
                # After RepairB, act has been tentatively placed.
                # Compute intrinsic utility with duration + conflict penalties.
                i_score, _, indiv_scores = interest_score(client, act)
                if indiv_scores:
                    avg_indiv = sum(indiv_scores.values()) / len(indiv_scores)
                else:
                    avg_indiv = i_score

                dur_pen = duration_penalty(act, client, avg_indiv)
                # IMPORTANT: still use *current* tags_encountered (before bumping for this act)
                conf_pen = conflict_penalty(act, client, tags_encountered)
                intrinsic = max(i_score - dur_pen - conf_pen, 0.0)

                if cfg.use_budget:
                    projected_spent = _spent_today(plan)
                    over = max(0.0, projected_spent - reserved_cap)
                    net = intrinsic - LAMBDA_BUDGET * over

                    if (over == 0.0) or (over > 0.0 and net >= SCORE_THRESHOLD):
                        _bump_tags(tags_encountered, act)
                        break

                    # otherwise roll back: remove newly-added act and restore times
                    plan.events.pop()
                    for ev, s, e in snapshot:
                        ev.start_dt, ev.end_dt = s, e
                    continue
                else:
                    if intrinsic >= SCORE_THRESHOLD:
                        _bump_tags(tags_encountered, act)
                        break

                    # intrinsic too low → rollback RepairB changes
                    plan.events.pop()
                    for ev, s, e in snapshot:
                        ev.start_dt, ev.end_dt = s, e
                    continue


    # ─────────────────────────────────────────────────────────────────────
    # 7) Finalize
    # ─────────────────────────────────────────────────────────────────────
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
    inter_end = min(a2, b2)
    return int((inter_end - inter_start).total_seconds() // 60)


def _future_candidates(activity: Activity,
                       day: date,
                       after_dt: datetime) -> List[datetime]:
    """Feasible future starts for this activity strictly after `after_dt`."""
    step = choose_step_minutes(activity) or 60
    cands = generate_candidate_times(activity, day, step_minutes=step)
    return [t for t in cands if t > after_dt]


def _can_place_against(
    events: List[PlanEvent],
    client: Client,
    act: Activity,
    when: datetime,
    cfg: Optional[PlannerConfig] = None,
) -> bool:
    """Hard checks + no-overlap against `events`."""
    cfg = cfg or PlannerConfig()

    if cfg.use_hard_constraints and not hard_feasible(client, act, when):
        return False
    if not fits_no_overlap(events, when, act):
        return False
    if cfg.use_weather and not is_weather_suitable(act, when):
        return False
    # day window is always respected (otherwise plans get weird)
    if not fits_in_window(act, client, when.hour * 60 + when.minute):
        return False
    return True



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
                       max_moves: int,
                       cfg: Optional[PlannerConfig] = None) -> bool:
    """
    Try moving `ev` forward by up to `max_moves` later candidate starts.
    If a move makes space, place (target_act @ target_start) and return True.
    Reverts the move if it didn't help.
    """
    cfg = cfg or PlannerConfig()

    if ev.activity.fixed_times:  # anchors don't move
        return False

    others = [x for x in plan.events if x is not ev]
    old_start, old_end = ev.start_dt, ev.end_dt

    tried = 0
    for t2 in _future_candidates(ev.activity, day, after_dt=ev.start_dt):
        if tried >= max_moves:
            break

        if _can_place_against(others, client, ev.activity, t2, cfg):
            # tentatively move the blocker
            ev.start_dt = t2
            ev.end_dt = t2 + timedelta(minutes=ev.activity.duration_min)

            # did that free the slot for E?
            if _can_place_against(plan.events, client, target_act, target_start, cfg):
                plan.add(PlanEvent(target_act, target_start))
                return True

            # revert and try next t2
            ev.start_dt, ev.end_dt = old_start, old_end

        tried += 1

    return False



def _flexibility_now(plan: PlanDay,
                     client: Client,
                     ev: PlanEvent,
                     day: date,
                     cfg: Optional[PlannerConfig] = None) -> int:
    """
    Approx count of alternative feasible starts (forward only) available
    to `ev` right now (excluding fixed-times).
    """
    cfg = cfg or PlannerConfig()

    if ev.activity.fixed_times:
        return 0
    others = [x for x in plan.events if x is not ev]
    count = 0
    for t2 in _future_candidates(ev.activity, day, after_dt=ev.start_dt):
        if _can_place_against(others, client, ev.activity, t2, cfg):
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
            try_others: bool = True,
            config: Optional[PlannerConfig] = None) -> bool:
    """
    Try to place `act` at `start_dt` by minimally adjusting existing events.

    1) Identify the event that most directly conflicts (max overlap minutes)
       and try nudging it forward up to `max_moves` later feasible starts.
    2) If that fails and `try_others` is True, try nudging other non-fixed events,
       ordered by least flexibility first (each by up to `max_moves` moves).
    Returns True iff `act` was placed.
    """
    cfg = config or PlannerConfig()

    conflicts = _blocking_events(plan.events, start_dt, act)
    if not conflicts:
        # defensive: if caller mis-signaled, just place the event
        plan.add(PlanEvent(act, start_dt))
        return True

    # 1) Direct conflicting event: the one with max overlap
    direct = max(conflicts, key=lambda ev: _overlap_minutes(start_dt, act, ev))
    if _try_nudge_forward(plan, client, direct, day, act, start_dt,
                          max_moves=max_moves, cfg=cfg):
        return True

    # 2) Optionally try other planned events (non-fixed), least flexibility first
    if try_others:
        candidates = [
            ev for ev in plan.events
            if (ev is not direct and not ev.activity.fixed_times)
        ]
        candidates.sort(key=lambda ev: _flexibility_now(plan, client, ev, day, cfg))

        for ev in candidates:
            if _try_nudge_forward(plan, client, ev, day, act, start_dt,
                                  max_moves=max_moves, cfg=cfg):
                return True

    return False



if __name__ == "__main__":
    from datetime import date, datetime, time
    from copy import deepcopy
    from .utils import load_people, load_events

    # ─────────────────────────────────────────────────────────────────────────────
    # Config presets for experiments
    # ─────────────────────────────────────────────────────────────────────────────
    EXPERIMENT_CONFIGS = [
        (
            "FULL_DEFAULT",
            PlannerConfig(
                use_hard_constraints=True,
                use_weather=True,
                use_budget=True,
                use_meals=True,
                use_base_plan=True,
                use_repairB=True,
                debug_print=False,  # set True to see anchor/repair logs
            ),
        ),
        (
            "NO_WEATHER",
            PlannerConfig(
                use_hard_constraints=True,
                use_weather=False,
                use_budget=True,
                use_meals=True,
                use_base_plan=True,
                use_repairB=True,
                debug_print=False,
            ),
        ),
        (
            "NO_BUDGET",
            PlannerConfig(
                use_hard_constraints=True,
                use_weather=True,
                use_budget=False,
                use_meals=True,
                use_base_plan=True,
                use_repairB=True,
                debug_print=False,
            ),
        ),
        (
            "NO_BASEPLAN",
            PlannerConfig(
                use_hard_constraints=True,
                use_weather=True,
                use_budget=True,
                use_meals=True,
                use_base_plan=False,   # Yash beam search OFF
                use_repairB=True,
                debug_print=False,
            ),
        ),
        (
            "NO_REPAIR",
            PlannerConfig(
                use_hard_constraints=True,
                use_weather=True,
                use_budget=True,
                use_meals=True,
                use_base_plan=True,
                use_repairB=False,     # RepairB OFF
                debug_print=False,
            ),
        ),
    ]

    def _print_plan(plan: PlanDay, cfg_name: str, day: date, client_name: str):
        print(f"\n[{client_name}] Plan for {day}  (config={cfg_name})")
        for ev in plan.events:
            print(
                f"- {ev.start_dt.time()}–{ev.end_dt.time()}  "
                f"{ev.activity.name} ({ev.activity.category})  "
                f"${ev.activity.cost_cad}"
            )

    # ─────────────────────────────────────────────────────────────────────────────
    # Helpers: read / clamp party ages to satisfy an activity's (amin..amax)
    # ─────────────────────────────────────────────────────────────────────────────
    def _party_ages(c) -> list[int]:
        ages = []
        # single traveler
        if isinstance(getattr(c, "age", None), (int, float)):
            ages.append(int(c.age))
        # groups: travellers / travelers (objects or dicts)
        for attr in ("travellers", "travelers"):
            grp = getattr(c, attr, None)
            if not grp:
                continue
            for p in grp:
                a = getattr(p, "age", None)
                if a is None and isinstance(p, dict):
                    a = p.get("age")
                if isinstance(a, (int, float)):
                    ages.append(int(a))
        return ages

    def _all_within_bounds(c, lo: int, hi: int) -> bool:
        ages = _party_ages(c)
        return bool(ages) and all(lo <= a <= hi for a in ages)

    def _clamp_party_ages(c, lo: int, hi: int):
        # Single traveler
        if isinstance(getattr(c, "age", None), (int, float)):
            c.age = max(lo, min(int(c.age), hi))

        # Your actual schema: adults_ages + kids_ages
        adults = getattr(c, "adults_ages", None)
        if isinstance(adults, list):
            c.adults_ages = [max(lo, min(int(a), hi)) for a in adults]

        kids = getattr(c, "kids_ages", None)
        if isinstance(kids, list):
            c.kids_ages = [max(lo, min(int(k), hi)) for k in kids]

        # Legacy: groups with travellers/travelers
        for attr in ("travellers", "travelers"):
            grp = getattr(c, attr, None)
            if not grp:
                continue
            for p in grp:
                if hasattr(p, "age"):
                    pa = getattr(p, "age", None)
                    if isinstance(pa, (int, float)):
                        setattr(p, "age", max(lo, min(int(pa), hi)))
                    else:
                        setattr(p, "age", max(lo, min(25, hi)))
                elif isinstance(p, dict):
                    pa = p.get("age")
                    if isinstance(pa, (int, float)):
                        p["age"] = max(lo, min(int(pa), hi))
                    else:
                        p["age"] = max(lo, min(25, hi))

    # ─────────────────────────────────────────────────────────────────────────────
    # Setup (PRESERVED): load data
    # ─────────────────────────────────────────────────────────────────────────────
    people = load_people()
    events = load_events()

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 1: Rainy subset + mock rainy walk, run under all configs
    # ─────────────────────────────────────────────────────────────────────────────
    client = people[0]
    day = date(2025, 8, 3)  # Arijit concert fixed at 17:00 on this date

    # Existing subset of events (PRESERVED)
    wanted_ids = {
        "e_st_lawrence_01",
        "e_rom_01",
        "e_ago_01",
        "e_distillery_01",
        "e_cn_tower_01",
        "e_concert_southasian_01",
    }
    subset = [e for e in events if e.id in wanted_ids]

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
        "popularity": 0.5,
    }

    # Simulate rainy conditions for testing (PRESERVED)
    current_weather = "Heavy rain"

    # Add mock event to the subset (PRESERVED)
    mock_rain_activity = Activity(**mock_rain_event)
    subset.append(mock_rain_activity)

    # Filter events based on *current_weather* label (just for comparison prints)
    filtered_subset = [
        e for e in subset
        if current_weather not in getattr(e, "weather_blockers", [])
    ]

    print("Subset BEFORE weather filter:")
    for e in subset:
        print(f"- {e.name} (weather blockers:{str(e.weather_blockers)}")

    print("\nSubset AFTER simple weather label filter:")
    for e in filtered_subset:
        print(f"- {e.name}")

    for a in filtered_subset:
        print(
            a.name,
            "interest=", interest_score(client, a),
            "base_value=", base_value(client, a),
            "cost=", a.cost_cad,
        )

    # ── Ensure ages satisfy concert bounds for THIS run too (PRESERVED)
    concert = next(
        (e for e in filtered_subset if e.id == "e_concert_southasian_01"),
        None,
    )
    if concert:
        # normalize missing bounds/duration
        if getattr(concert, "age_min", None) in (None, ""):
            concert.age_min = 0
        if getattr(concert, "age_max", None) in (None, ""):
            concert.age_max = 120
        if getattr(concert, "duration_min", None) in (None, 0):
            concert.duration_min = 120
        amin, amax = int(concert.age_min), int(concert.age_max)

        # pick an existing client whose whole party fits; else clone & clamp
        chosen = None
        for p in people:
            if _all_within_bounds(p, amin, amax):
                chosen = p
                break
        if chosen is None:
            chosen = deepcopy(people[0])
            _clamp_party_ages(chosen, amin, amax)
        client = chosen
        ages_str = ", ".join(map(str, _party_ages(client))) or "unknown"
        print(f"[test] Using client with party ages=[{ages_str}] (allowed {amin}-{amax})")

    # Run SCENARIO 1 with EACH config
    for cfg_name, cfg in EXPERIMENT_CONFIGS:
        print(f"\n========== SCENARIO 1: RAINY SUBSET (config={cfg_name}) ==========")
        plan = make_day_plan(client, filtered_subset, day, config=cfg)
        _print_plan(plan, cfg_name, day, getattr(client, "name", "Client"))

    # ─────────────────────────────────────────────────────────────────────────────
    # EXTRA SCENARIOS: Family & Couple, using ALL GTA events (no whitelist)
    # Meteo-safe: roll scenario days + shift any explicit fixed dates into horizon
    # ─────────────────────────────────────────────────────────────────────────────

    # === Meteo forecast horizon handling ===
    HORIZON_DAYS = 14           # Open-Meteo reliable forecast window
    BASE_OFFSET_DAYS = 2        # start runs ~2 days from "today"

    today = date.today()
    _ROLLED_DAY0 = today + timedelta(days=min(BASE_OFFSET_DAYS, HORIZON_DAYS - 1))
    _ROLLED_DAY1 = min(_ROLLED_DAY0 + timedelta(days=1), today + timedelta(days=HORIZON_DAYS - 1))

    def _parse_dt_str_maybe(s: str) -> tuple[date | None, str | None]:
        s = s.strip()
        # "YYYY-MM-DD HH:MM"
        if " " in s:
            dpart, tpart = s.split(None, 1)
            try:
                y, m, d_ = map(int, dpart.split("-"))
                datetime(y, m, d_)  # validate
                return date(y, m, d_), tpart
            except Exception:
                return None, None
        # "YYYY-MM-DD"
        try:
            y, m, d_ = map(int, s.split("-"))
            datetime(y, m, d_)  # validate
            return date(y, m, d_), None
        except Exception:
            return None, None

    def _retarget_fixed_times_into_horizon(evts: list[Activity], base_start: date):
        """
        Find earliest explicit fixed-date across `evts`; shift all explicit fixed-dates
        by a constant delta so that earliest lands on `base_start`. Keeps relative gaps.
        Accepts dict {"date":"YYYY-MM-DD","start":"HH:MM"} and strings "YYYY-MM-DD" or "YYYY-MM-DD HH:MM".
        """
        explicit_dates: list[date] = []

        # Collect explicit dates
        for a in evts:
            fts = getattr(a, "fixed_times", None)
            if not fts:
                continue
            if isinstance(fts, dict):
                dstr = fts.get("date")
                if dstr:
                    try:
                        y, m, d_ = map(int, dstr.split("-"))
                        explicit_dates.append(date(y, m, d_))
                    except Exception:
                        pass
            elif isinstance(fts, list):
                for it in fts:
                    if isinstance(it, dict) and it.get("date"):
                        try:
                            y, m, d_ = map(int, it["date"].split("-"))
                            explicit_dates.append(date(y, m, d_))
                        except Exception:
                            pass
                    elif isinstance(it, str):
                        dmaybe, _ = _parse_dt_str_maybe(it)
                        if dmaybe:
                            explicit_dates.append(dmaybe)

        if not explicit_dates:
            return  # nothing to shift

        oldest = min(explicit_dates)
        delta = base_start - oldest

        def _shift_date_str(dstr: str) -> str:
            y, m, d_ = map(int, dstr.split("-"))
            return (date(y, m, d_) + delta).isoformat()

        # Apply shift
        for a in evts:
            fts = getattr(a, "fixed_times", None)
            if not fts:
                continue

            if isinstance(fts, dict):
                if fts.get("date"):
                    fts = dict(fts)
                    fts["date"] = _shift_date_str(fts["date"])
                    setattr(a, "fixed_times", fts)
                continue

            if isinstance(fts, list):
                new_list = []
                for it in fts:
                    if isinstance(it, dict) and it.get("date"):
                        it = dict(it)
                        it["date"] = _shift_date_str(it["date"])
                        new_list.append(it)
                    elif isinstance(it, str):
                        dmaybe, tmaybe = _parse_dt_str_maybe(it)
                        if dmaybe:
                            newd = (dmaybe + delta).isoformat()
                            new_list.append(f"{newd} {tmaybe}" if tmaybe else newd)
                        else:
                            new_list.append(it)
                    else:
                        new_list.append(it)
                setattr(a, "fixed_times", new_list)

    GTA_CITIES = {
        "Toronto","Etobicoke","North York","Scarborough","York","East York",
        "Mississauga","Brampton","Vaughan","Markham","Richmond Hill",
        "Oakville","Pickering","Ajax","Whitby"
    }

    # Use every event in GTA so the new activities are in play
    all_gta_events = [e for e in events if getattr(e, "city", "") in GTA_CITIES]

    # Normalize a bit for safety
    for a in all_gta_events:
        if getattr(a, "duration_min", None) in (None, 0):
            a.duration_min = 90
        if getattr(a, "age_min", None) in (None, ""):
            a.age_min = 0
        if getattr(a, "age_max", None) in (None, ""):
            a.age_max = 120
        if getattr(a, "fixed_times", None) is None:
            a.fixed_times = []
        if getattr(a, "weather_blockers", None) is None:
            a.weather_blockers = []

    # Shift any explicit fixed dates inside the forecast horizon
    _retarget_fixed_times_into_horizon(all_gta_events, _ROLLED_DAY0)

    # 2-day window inside horizon
    day1 = _ROLLED_DAY0
    day2 = _ROLLED_DAY1

    def _mk_family(base_client):
        fam = deepcopy(base_client)
        fam.name = getattr(fam, "name", "Family (Demo)")
        fam.adults_ages = [34, 33]
        fam.kids_ages = [12, 8]
        fam.budget_total = getattr(fam, "budget_total", 400.0) or 400.0
        if not getattr(fam, "home_base", None):
            class _Loc: ...
            fam.home_base = _Loc()
            fam.home_base.lat, fam.home_base.lng = 43.653, -79.383
            fam.home_base.city = "Toronto"
        fam.meal_prefs = {
            "breakfast": {"window": ["08:00","10:00"], "cuisines": ["bakery","brunch","coffee"]},
            "lunch":     {"window": ["12:00","14:00"], "cuisines": ["pizza","burgers","shawarma"]},
            "dinner":    {"window": ["18:00","20:30"], "cuisines": ["italian","indian","chinese"]},
        }
        fam.dietary = {
            "vegetarian": False, "vegan": False, "halal": False, "kosher": False,
            "gluten_free": False, "dairy_free": False, "nut_allergy": False,
            "avoid": [], "required_terms": [],
        }
        fam.trip_start, fam.trip_end = day1, day2
        return fam

    def _mk_couple(base_client):
        cp = deepcopy(base_client)
        cp.name = getattr(cp, "name", "Couple (Demo)")
        cp.adults_ages = [28, 27]
        cp.kids_ages = []
        cp.budget_total = getattr(cp, "budget_total", 300.0) or 300.0
        if not getattr(cp, "home_base", None):
            class _Loc: ...
            cp.home_base = _Loc()
            cp.home_base.lat, cp.home_base.lng = 43.653, -79.383
            cp.home_base.city = "Toronto"
        cp.meal_prefs = {
            "breakfast": {"window": ["09:00","10:30"], "cuisines": ["coffee","brunch"]},
            "lunch":     {"window": ["12:30","14:00"], "cuisines": ["sushi","ramen","tacos"]},
            "dinner":    {"window": ["19:00","21:00"], "cuisines": ["steak","italian","thai"]},
        }
        cp.dietary = {
            "vegetarian": False, "vegan": False, "halal": False, "kosher": False,
            "gluten_free": False, "dairy_free": False, "nut_allergy": False,
            "avoid": [], "required_terms": [],
        }
        cp.trip_start, cp.trip_end = day1, day2
        return cp

    # Base to clone from
    base_for_clone = client if "client" in locals() else (people[0] if people else None)
    if base_for_clone is None:
        raise RuntimeError("No base client to clone from; ensure load_people() returned at least one entry.")

    # Create family & couple
    family_client = _mk_family(base_for_clone)
    couple_client = _mk_couple(base_for_clone)

    # Helper to plan + print for a given client and day under all configs
    def _run_plan_for(client_obj, acts, d):
        """
        Run the SAME client/day/activities under each config
        and print the plans. Returns a dict config_name -> PlanDay.
        """
        amin_day = min(int(getattr(a, "age_min", 0) or 0) for a in acts) if acts else 0
        amax_day = max(int(getattr(a, "age_max", 120) or 120) for a in acts) if acts else 120
        _clamp_party_ages(client_obj, amin_day, amax_day)

        plans = {}
        for cfg_name, cfg in EXPERIMENT_CONFIGS:
            print(
                f"\n[{getattr(client_obj, 'name', 'Client')}] "
                f"Plan for {d} (config={cfg_name})"
            )
            planX = make_day_plan(client_obj, acts, d, config=cfg)
            for ev in planX.events:
                print(
                    f"- {ev.start_dt.time()}–{ev.end_dt.time()}  "
                    f"{ev.activity.name} ({ev.activity.category})  "
                    f"${ev.activity.cost_cad}"
                )
            plans[cfg_name] = planX
        return plans

    # FAMILY: consider ALL GTA events under all configs
    print("\n========== FAMILY (ALL GTA EVENTS) ==========")
    fam_plans_d1 = _run_plan_for(family_client, all_gta_events, day1)
    fam_plans_d2 = _run_plan_for(family_client, all_gta_events, day2)

    # COUPLE: consider ALL GTA events under all configs
    print("\n========== COUPLE (ALL GTA EVENTS) ==========")
    cpl_plans_d1 = _run_plan_for(couple_client, all_gta_events, day1)
    cpl_plans_d2 = _run_plan_for(couple_client, all_gta_events, day2)

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 3: Rolled subset (concert + set) inside forecast horizon
    # ─────────────────────────────────────────────────────────────────────────────
    day = _ROLLED_DAY0  # instead of hard-coded 2025-08-03

    wanted_ids = {
        "e_st_lawrence_01",
        "e_rom_01",
        "e_ago_01",
        "e_distillery_01",
        "e_cn_tower_01",
        "e_concert_southasian_01",
    }
    subset = [e for e in events if e.id in wanted_ids]

    # Shift fixed dates for this subset too
    _retarget_fixed_times_into_horizon(subset, _ROLLED_DAY0)

    # Pull the concert to read age bounds / set sane defaults (PRESERVED)
    concert = next((e for e in subset if e.id == "e_concert_southasian_01"), None)
    if not concert:
        raise RuntimeError("Concert e_concert_southasian_01 not found in events!")

    if getattr(concert, "age_min", None) in (None, ""):
        concert.age_min = 0
    if getattr(concert, "age_max", None) in (None, ""):
        concert.age_max = 120
    if getattr(concert, "duration_min", None) in (None, 0):
        concert.duration_min = 120

    amin = int(concert.age_min)
    amax = int(concert.age_max)

    client = None
    for p in people:
        if _all_within_bounds(p, amin, amax):
            client = p
            break
    if client is None:
        client = deepcopy(people[0])
        _clamp_party_ages(client, amin, amax)

    print(f"[test] Using client age(s)={_party_ages(client)} (allowed {amin}-{amax})")

    def _show_fixed(a):
        ft = getattr(a, "fixed_times", None)
        return ft if ft is not None else []

    print(
        "ANCHORS:",
        [
            (a.id, type(getattr(a, "fixed_times", None)).__name__, _show_fixed(a))
            for a in subset
            if getattr(a, "fixed_times", None)
        ],
    )

    # Run SCENARIO 3 with EACH config
    for cfg_name, cfg in EXPERIMENT_CONFIGS:
        print(f"\n========== SCENARIO 3: ROLLED SUBSET (config={cfg_name}) ==========")
        plan = make_day_plan(client, subset, day, config=cfg)
        _print_plan(plan, cfg_name, day, getattr(client, "name", "Client"))

