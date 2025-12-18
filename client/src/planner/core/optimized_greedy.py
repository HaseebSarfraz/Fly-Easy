# src/planner/core/solver.py
from datetime import date, datetime, timedelta  # MAKE SURE THIS IS INSTALLED
from typing import List  # MAKE SURE THIS IS INSTALLED
from planner.core.models import Client, Activity, PlanDay, PlanEvent, Location
from planner.core.constraints import hard_feasible
from planner.core.timegrid import generate_candidate_times, choose_step_minutes
from planner.core.scoring import interest_score, duration_penalty, conflict_penalty
from heapq import heappush, heappop

import requests  # TO MAKE API REQUESTS (MUST BE INSTALLED ON DEVICE)
import pandas as pd  # MAKE SURE THIS IS INSTALLED ON THE DEVICE

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


# ───────────── WEATHER CHECK WITH CACHE ─────────────
def is_weather_suitable(activity: Activity, start_dt: datetime) -> bool:
    wb = activity.weather_blockers
    if not wb:
        return True

    end_dt = start_dt + timedelta(minutes=activity.duration_min)
    tz = get_timezone(activity.city)

    # Use cache key based on location + date
    cache_key = (activity.location.lat, activity.location.lng, start_dt.date())
    if cache_key in weather_cache:
        data = weather_cache[cache_key]
    else:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": activity.location.lat,
            "longitude": activity.location.lng,
            "hourly": "weathercode",
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "timezone": tz
        }
        response = requests.get(url, params=params)
        data = response.json()
        weather_cache[cache_key] = data  # store in cache

    times = pd.to_datetime(data["hourly"]["time"])
    weather_codes = data["hourly"]["weathercode"]

    event_mask = (times >= start_dt) & (times <= end_dt)
    event_weather_codes = [weather_codes[i] for i, m in enumerate(event_mask) if m]
    event_weather = [WEATHER_CODE_MAP[code] for code in event_weather_codes]

    return not any(w in activity.weather_blockers for w in event_weather)


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


def _make_day_plan_helper(client: Client, activities: List[Activity], day: date) -> PlanDay:
    """
    Helper function to make a day plan.
    This helper is used multiple times for layered-scoring and planning.
    """
    plan = PlanDay(day)
    engagement_time = client.engagement_time.copy()
    for act in activities:
        step = choose_step_minutes(act) or 60
        for start_dt in generate_candidate_times(act, day, step_minutes=step):
            # Checks if the age restriction and start time is feasible based on
            # when client starts and the duration of the activity with respect to its closing time
            start_min = start_dt.hour * 60 + start_dt.minute
            if not (client.day_start_min <= start_min < client.day_end_min):
                continue  # skip times outside client day
            _, _, individual_scores = interest_score(client, act)

            if sum(individual_scores.values()) == 0:
                continue
            time_allocation = _allocate_time_by_interest(act, individual_scores)
            hard_check = hard_feasible(client, act, start_dt)
            no_overlap = fits_no_overlap(plan.events, start_dt, act)
            window_fits = fits_in_window(act, client, start_dt.hour * 60 + start_dt.minute)
            can_add_time = all(
                engagement_time[p] + t <= client.daily_act_time_per_member
                for p, t in time_allocation.items()
            )
            if no_overlap and hard_check and window_fits and can_add_time:
                if is_weather_suitable(act, start_dt):  # ONLY RUNS WEATHER CHECKS IF THE EVENT CAN FIT (OPTIMIZATION)
                    plan.add(PlanEvent(act, start_dt))
                    for p, t in time_allocation.items():
                        engagement_time[p] += t
                    break

            placed = repairB(plan, client, act, day, start_dt, engagement_time, max_moves=1, try_others=True)

            if placed:
                break  # E placed; move to next activity
            # else: try next candidate time for this act

    return plan


def _allocate_time_by_interest(act, interest_scores, beta=1.3) -> dict:
    """
    Helper function to compute the time allocated per-member for this activity.
    """
    duration = act.duration_min
    max_interest = max(interest_scores.values())
    most_interested = [m for m, s in interest_scores.items() if max_interest == interest_scores[m]][0]
    fair_pen_factors = {m: (score / 10) ** beta for m, score in interest_scores.items() if score > 0}  # EXPONENTIAL PENALTY FACTORS
    total_weight = float(sum(fair_pen_factors.values()))  # TOTAL INTEREST SCORES
    member_time_allocation = {
        m: duration * (w / total_weight) for m, w in fair_pen_factors.items()
    }
    if len(member_time_allocation) < len(interest_scores):
        member_time_allocation[most_interested] += (duration - sum(member_time_allocation.values()))
    return member_time_allocation


def _build_base_plan(client, activities, threshold=0.75, beam=8) -> list[list[Activity]]:
    """
    Helper function to build a base-plan.
    """
    candidates = []

    # Precompute interest sets
    for act in activities:
        interested = set()
        score = 0

        for person in client.party_members:
            iw = sum(client.interest(tag, person) for tag in act.tags)
            if iw > 0:
                max_possible = 10 * len(act.tags)

                # PREVENTS ACTIVITIES FROM BEING ADDED IF THEY EXCEED EACH MEMBER'S TIMING
                if (iw / max_possible >= threshold and
                        act.duration_min / client.total_day_duration <= client.daily_act_time_per_member):
                    interested.add(person)
                    score += iw

        if interested:
            candidates.append((act, interested, score))

    # Sort strong candidates first
    candidates.sort(key=lambda x: (len(x[1]), x[2]), reverse=True)

    # Beam search
    plans = [([], set(), 0)]  # (activities, satisfied_people, score)

    for act, interested, score in candidates:
        new_plans = []

        for acts, sat, s in plans:
            # Option 1: skip
            new_plans.append((acts, sat, s))

            # Option 2: take if it adds value
            new_people = interested - sat
            if new_people:
                new_plans.append((
                    acts + [act],
                    sat | new_people,
                    s + score
                ))

        # Prune
        new_plans.sort(
            key=lambda p: (len(p[1]), p[2]),
            reverse=True
        )
        plans = new_plans[:beam]

    return [p[0] for p in plans]  # base PLANS


def make_day_plan(client: Client, activities: List[Activity], day: date) -> PlanDay:
    # --- Using beam search, generate the 8 best base plans (this aims to maximize overall base satisfaction)  ---
    BEAM = 8
    base_plans = _build_base_plan(client, activities, threshold=0.75, beam=BEAM)

    final_plan = None
    # Try each base plan in order
    for candidate_acts in base_plans:
        plan = _make_day_plan_helper(client, candidate_acts, day)
        # Check if all base activities were successfully placed
        if len(plan.events) == len(candidate_acts):
            final_plan = plan
            break
        # Otherwise, continue to next candidate
    if final_plan is None:
        # None of the base plans could be fully placed; pick the first one anyway and try to repair
        final_plan = _make_day_plan_helper(client, base_plans[0], day)

    # --- Step 2: Prepare remaining activities for normal scheduling ---
    scheduled_ids = {ev.activity.id for ev in final_plan.events}
    remaining_activities = [act for act in activities if act.id not in scheduled_ids]

    # Build a heap of remaining activities by group interest
    act_heap = []
    tags_encountered = {"concerts": 0,
                        "food": 0,
                        "nightlife": 0,
                        "history": 0,
                        "museums": 0,
                        "architecture": 0,
                        "aquarium": 0,
                        "theme_parks": 0,
                        "zoo": 0,
                        "parks": 0,
                        "islands": 0,
                        "shopping": 0,
                        "pizza": 0,
                        "theatre": 0,
                        "views": 0}  # track tags seen so far (USED FOR CONFLICT_PENALTY)
    engagement_time = client.engagement_time.copy()

    for ind, act in enumerate(remaining_activities):
        i_score, e_creds, ii_score = interest_score(client, act)
        if sum(ii_score.values()) == 0:
            continue
        avg_score = sum(ii_score.values())/len(ii_score)
        i_score = max(i_score - duration_penalty(act, client, avg_score), 0)
        # LINE BELOW STORES THE CURRENT ACTIVITY BY INTEREST SCORE, THEN ALSO STORES EACH MEMBERS EXT_CREDS IF ANY
        conf_penalty = conflict_penalty(act, client, tags_encountered)
        i_score = max(i_score - conf_penalty, 0)
        time_allocation = _allocate_time_by_interest(act, ii_score)
        heappush(act_heap, (-i_score, ind, act, e_creds, ii_score, time_allocation))
        for tag in act.tags:
            tags_encountered.setdefault(tag, 0)
            tags_encountered[tag] += 1
            # PENALIZES REPETITIVE ACTIVITIES. WE ARE SCHEDULING BASED ON A PRIORITY-FIRST BASIS ANYWAY SO THIS IS FINE.

    # --- Step 3: Try to place remaining activities ---
    while act_heap:
        iscore, _, act, ecreds, iiscore, time_allocation = heappop(act_heap)
        step = choose_step_minutes(act) or 60

        for start_dt in generate_candidate_times(act, day, step_minutes=step):
            start_min = start_dt.hour * 60 + start_dt.minute
            if not (client.day_start_min <= start_min < client.day_end_min):
                continue
            hard_check = hard_feasible(client, act, start_dt)
            no_overlap = fits_no_overlap(final_plan.events, start_dt, act)
            window_fits = fits_in_window(act, client, start_min)
            ext_creds_usable = len(ecreds) > 0 and all([c - ecreds.get(p, 0) >= 0 for p, c in client.credits_left.items()])

            # IF THIS ACTIVITY CAN ALLOCATE SUFFICIENT TIME PER MEMBER THROUGHOUT THE DAY.
            can_add_time = all([time_allocation[p] + client.engagement_time[p] < client.daily_act_time_per_member for p in time_allocation])

            try_repair = False
            if no_overlap and hard_check and window_fits and can_add_time:
                if is_weather_suitable(act, start_dt):
                    final_plan.add(PlanEvent(act, start_dt))
                    if ext_creds_usable:
                        for p, c in ecreds.items():
                            client.credits_left[p] -= c  # UPDATES THE REMAINING CREDITS LEFT FOR THE CLIENT
                    break
                try_repair = True
            if try_repair:
                placed = repairB(final_plan, client, act, day, start_dt, engagement_time, max_moves=1, try_others=True)
                if placed:
                    break
    final_plan.events.sort(key=lambda ev: ev.start_dt)
    return final_plan


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


def _can_place_against(events: List[PlanEvent],
                       client: Client,
                       act: Activity,
                       when: datetime) -> bool:
    """Hard checks + no-overlap against `events`."""
    return (hard_feasible(client, act, when) and fits_no_overlap(events, when, act) and is_weather_suitable(act, when)
            and fits_in_window(act, client, when.hour * 60 + when.minute))


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
            ev.end_dt = t2 + timedelta(minutes=ev.activity.duration_min)

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
            engagement_time: dict,
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
        time_allocation = _allocate_time_by_interest(act, individual_scores)
        if not all(
                engagement_time[p] + t <= client.daily_act_time_per_member
                for p, t in time_allocation.items()
        ):
            return False
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

    # --------------------------------------------------
    # RUN PLANNER
    # --------------------------------------------------
    test_day = date(2025, 11, 23)
    plan = make_day_plan(client, events, test_day)

    # --------------------------------------------------
    # SCORE BREAKDOWN
    # --------------------------------------------------
    print(f"\n📅 FINAL PLAN FOR {test_day}\n" + "-" * 60)

    tags_count = {}
    for ev in plan.events:
        act = ev.activity
        iscore, ext_creds, individual_scores = interest_score(client, act)
        dur_pen = duration_penalty(act, client, iscore)
        time_split = _allocate_time_by_interest(act, individual_scores)
        conf_pen = conflict_penalty(act, client, tags_count)
        final_score = max((iscore - dur_pen) - conf_pen, 0)

        print(f"\n▶ {act.name}")
        print(f"  Time: {ev.start_dt.time()}–{ev.end_dt.time()}")
        print(f"  Interest score:        {iscore:.2f}")
        print(f"  Duration penalty:     {dur_pen:.2f}")
        print(f"  Conflict penalty:     {conf_pen:.2f}")
        print(f"  FINAL SCORE:          {final_score:.2f}")

        print("  Time allocation:")
        for m, t in time_split.items():
            print(f"    {m}: {t:.1f} min")

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------
    print("\n✅ Scheduled activities:")
    for ev in plan.events:
        print(f"  - {ev.activity.name}")

    scheduled_ids = {ev.activity.id for ev in plan.events}
    rejected = [a for a in events if a.id not in scheduled_ids]

    print("\n❌ Rejected activities:")
    for a in rejected:
        print(f"  - {a.name}")
