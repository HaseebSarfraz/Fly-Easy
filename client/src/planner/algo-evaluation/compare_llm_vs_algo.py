#!/usr/bin/env python3
import json, sys
from datetime import datetime, date, timedelta
from collections import defaultdict

from planner.core.utils import load_people, load_events
from planner.core.optimized_greedy import make_day_plan, is_weather_suitable
from planner.core.scoring import interest_score, base_value


def _minutes(s: str) -> int:  # "YYYY-MM-DDTHH:MM" -> minutes from midnight
    t = datetime.fromisoformat(s)
    return t.hour * 60 + t.minute


def _overlap(a_start, a_dur, b_start, b_dur) -> bool:
    a1, a2 = a_start, a_start + a_dur
    b1, b2 = b_start, b_start + b_dur
    return not (a2 <= b1 or b2 <= a1)


def _index_events_by_id(events):
    return {e.id: e for e in events}


def _plan_from_algo(client, events, day: date):
    """
    Run our solver and normalize to the same schema as LLM output
    (id, start, duration_min, cost_cad, fixed).

    IMPORTANT: For fair eval, we drop any synthetic events (like meal_* or
    Google Places restaurants) that are not in `events`.
    """
    pd = make_day_plan(client, events, day)

    # Only keep events that exist in the original dataset
    valid_ids = {e.id for e in events}

    out = []
    for ev in pd.events:
        if ev.activity.id not in valid_ids:
            # skip synthetic / meal / external events during evaluation
            # print(f"[eval] skipping synthetic event {ev.activity.id}")
            continue

        out.append({
            "id": ev.activity.id,
            "start": ev.start_dt.strftime("%Y-%m-%dT%H:%M"),
            "duration_min": int(ev.activity.duration_min or 0),
            "cost_cad": float(ev.activity.cost_cad or 0.0),
            "fixed": bool(ev.activity.fixed_times),
        })
    return out



def _validate_hard(client, events_by_id, date_iso: str, sched):
    """
    Returns a list of error strings for any HARD constraint violations.

    Hard = exactly what the algo treats as hard:
      - unknown event id
      - no overlaps
      - age bounds
      - opening hours
      - weather blockers
      - fixed-time anchors must be at one of their fixed start times

    NOTE: client day window is treated as SOFT now and is handled in _soft_metrics.
    """
    errs = []

    # 1) Build list of events for overlap + per-event checks
    day_events = []
    for ev in sched:
        if ev["id"] not in events_by_id:
            errs.append(f"Unknown event id: {ev['id']}")
            continue
        e = events_by_id[ev["id"]]
        s_min = _minutes(ev["start"])
        dur = int(ev.get("duration_min", 0))

        # IMPORTANT: no client day-window check here anymore (soft only)
        day_events.append((s_min, dur, ev, e))

    # 2) No overlaps (hard)
    for i in range(len(day_events)):
        for j in range(i + 1, len(day_events)):
            if _overlap(day_events[i][0], day_events[i][1],
                        day_events[j][0], day_events[j][1]):
                errs.append(
                    f"Overlap: {day_events[i][2]['id']} "
                    f"vs {day_events[j][2]['id']}"
                )

    # 3) Age bounds, opening hours, weather, fixed-times (all hard)
    for s_min, dur, evj, e in day_events:
        # age bounds
        amin = int(getattr(e, "age_min", 0) or 0)
        amax = int(getattr(e, "age_max", 120) or 120)
        ages = []
        ages += getattr(client, "adults_ages", []) or []
        ages += getattr(client, "kids_ages", []) or []
        if not ages and hasattr(client, "age"):
            ages = [int(client.age)]
        for a in ages:
            if not (amin <= a <= amax):
                errs.append(
                    f"Age bound violated for {evj['id']} "
                    f"(age {a} not in [{amin},{amax}])"
                )
                break

        # opening hours simple check (daily window)
        oh = getattr(e, "opening_hours", None) or {}
        daily = oh.get("daily")
        if isinstance(daily, (list, tuple)) and len(daily) == 2:
            open_s = int(daily[0].split(":")[0]) * 60 + int(daily[0].split(":")[1])
            open_e = int(daily[1].split(":")[0]) * 60 + int(daily[1].split(":")[1])
            if not (open_s <= s_min and s_min + dur <= open_e):
                errs.append(f"Opening hours violated for {evj['id']}")

        # weather blockers
        try:
            y, m, d = map(int, date_iso.split("-"))
            start_dt = datetime(y, m, d) + timedelta(minutes=s_min)
            ok = is_weather_suitable(e, start_dt)
            if not ok:
                errs.append(f"Weather blocked: {evj['id']}")
        except Exception:
            # if weather metadata is missing or forecast fails, skip
            pass

        # fixed-time anchors must align
        ft = getattr(e, "fixed_times", None)

        def _to_min(hm: str) -> int:
            hh, mm = map(int, hm.split(":"))
            return hh * 60 + mm

        if ft:
            accepted = False
            if isinstance(ft, list):
                for item in ft:
                    if isinstance(item, str):
                        hm = item.strip().split()[-1]
                        if _to_min(hm) == s_min:
                            accepted = True
                    elif isinstance(item, dict) and "start" in item:
                        if _to_min(item["start"]) == s_min:
                            accepted = True
            elif isinstance(ft, dict) and "start" in ft:
                if _to_min(ft["start"]) == s_min:
                    accepted = True
            elif isinstance(ft, str):
                hm = ft.strip().split()[-1]
                if _to_min(hm) == s_min:
                    accepted = True
            if not accepted:
                errs.append(f"Fixed-time violation: {evj['id']} @ {evj['start']}")

    return errs


def _soft_metrics(client, events_by_id, sched, date_iso):
    """
    Compute soft metrics for a schedule:

    - interest_sum: total interest score (group satisfaction)
    - total_cost: total cost
    - utilization: fraction of the client's day that is "spanned" by the plan
    - n_events: number of events
    - distinct_events: unique event IDs (diversity)
    - budget_per_day: client's soft cap per day
    - budget_overrun: max(0, total_cost - budget_per_day)
    - day_window_violations: #events outside [client.day_start_min, client.day_end_min]
    """
    total_interest = 0.0
    total_cost = 0.0
    total_dur = 0

    first_start_min = None
    last_end_min = None

    ids = []

    # preferred client day window (SOFT)
    day_start = int(getattr(client, "day_start_min", 0) or 0)
    day_end = int(getattr(client, "day_end_min", 24 * 60) or (24 * 60))
    day_span = max(0, day_end - day_start)
    day_window_violations = 0

    for ev in sched:
        ev_id = ev.get("id")
        if not ev_id:
            continue
        ids.append(ev_id)

        e = events_by_id.get(ev_id)
        if not e:
            # unknown event id, skip for soft metrics
            continue

        # duration
        dur = int(ev.get("duration_min") or getattr(e, "duration_min", 0) or 0)
        total_dur += dur

        # cost
        cost = float(getattr(e, "cost_cad", 0.0) or 0.0)
        total_cost += cost

        # interest (group satisfaction)
        try:
            total_interest += interest_score(client, e)
        except Exception:
            # be robust; don't crash the whole eval if scoring blows up
            pass

        # utilization + soft day-window
        ts = ev.get("start")
        if not isinstance(ts, str):
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            continue

        s_min = dt.hour * 60 + dt.minute
        e_min = s_min + dur

        # track span for utilization
        if first_start_min is None or s_min < first_start_min:
            first_start_min = s_min
        if last_end_min is None or e_min > last_end_min:
            last_end_min = e_min

        # soft penalty if we leave the client day window
        if s_min < day_start or e_min > day_end:
            day_window_violations += 1

    # compute utilization as span / available day
    if first_start_min is not None and last_end_min is not None and day_span > 0:
        used_span = max(0, last_end_min - first_start_min)
        utilization = max(0.0, min(1.0, used_span / day_span))
    else:
        utilization = 0.0

    distinct_events = len(set(ids))

    # --- budget-related metrics ---
    budget_total = float(getattr(client, "budget_total", 0.0) or 0.0)
    try:
        ts = getattr(client, "trip_start", None)
        te = getattr(client, "trip_end", None)
        if ts and te:
            d0 = date.fromisoformat(ts)
            d1 = date.fromisoformat(te)
            n_days = max(1, (d1 - d0).days + 1)
        else:
            n_days = 1
    except Exception:
        n_days = 1

    if n_days > 0:
        budget_per_day = budget_total / n_days
    else:
        budget_per_day = budget_total

    budget_overrun = max(0.0, total_cost - budget_per_day)

    return {
        "interest_sum": total_interest,
        "total_cost": total_cost,
        "utilization": utilization,
        "n_events": len(ids),
        "distinct_events": distinct_events,
        "budget_per_day": budget_per_day,
        "budget_overrun": budget_overrun,
        "day_window_violations": day_window_violations,
    }


def _composite_score(hard_errors, metrics) -> float:
    """
    Combine hard + soft into a single score in [0,1].

    - Hard: 1 if no violations, otherwise 1/(1+violations).
    - Soft:
        * utilization (0..1)
        * budget_score (1 if under, decays if over)
        * diversity (distinct_events / n_events)
        * satisfaction (squashed interest_sum)
        * day-window score (1 if no violations, decreases with more)
    """
    # hard: reflect strict feasibility
    hard_score = 1.0 if not hard_errors else 1.0 / (1.0 + len(hard_errors))

    # budget
    budget_per_day = metrics["budget_per_day"]
    over = metrics["budget_overrun"]
    if budget_per_day > 0:
        budget_score = 1.0 / (1.0 + over / budget_per_day)
    else:
        budget_score = 1.0

    # diversity
    if metrics["n_events"] > 0:
        diversity = metrics["distinct_events"] / metrics["n_events"]
    else:
        diversity = 0.0

    # utilization
    util = metrics["utilization"]

    # satisfaction (squash interest_sum → [0,1))
    if metrics["interest_sum"] > 0:
        sat = metrics["interest_sum"] / (metrics["interest_sum"] + 10.0)
    else:
        sat = 0.0

    # soft day-window score
    wv = metrics.get("day_window_violations", 0)
    if wv <= 0:
        window_score = 1.0
    else:
        window_score = 1.0 / (1.0 + wv)

    # weights chosen to roughly reflect your priorities:
    soft_score = (
        0.25 * util +
        0.20 * budget_score +
        0.20 * diversity +
        0.25 * sat +
        0.10 * window_score
    )

    return 0.6 * hard_score + 0.4 * soft_score


def main():

    if len(sys.argv) >= 2:
        llm_path = sys.argv[1]
    else:
        llm_path = "src/planner/algo-evaluation/runs/claude_planner.json"

    with open(llm_path, "r", encoding="utf-8") as f:
        llm_json = json.load(f)

    plans = llm_json.get("plans", [])

    people = load_people()
    events = load_events()
    events_by_id = _index_events_by_id(events)
    people_by_name = {getattr(p, "name", "Client"): p for p in people}

    # Group LLM plans by (client,date)
    llm_map = defaultdict(list)
    for entry in plans:
        key = (entry["client"], entry["date"])
        llm_map[key] = entry["events"]

    # Aggregates for summary
    total_days = 0
    sum_llm_score = 0.0
    sum_algo_score = 0.0
    hard_valid_days_llm = 0
    hard_valid_days_algo = 0

    # For each (client,date) in LLM output, build our algo plan and compare
    for (client_name, date_iso), llm_sched in llm_map.items():
        client = people_by_name.get(client_name) or people[0]
        y, m, d = map(int, date_iso.split("-"))
        algo_sched = _plan_from_algo(client, events, date(y, m, d))

        # Hard-constraint validation for both
        llm_hard_errors = _validate_hard(client, events_by_id, date_iso, llm_sched)
        algo_hard_errors = _validate_hard(client, events_by_id, date_iso, algo_sched)

        # Soft metrics
        llm_soft = _soft_metrics(client, events_by_id, llm_sched, date_iso)
        algo_soft = _soft_metrics(client, events_by_id, algo_sched, date_iso)

        # Composite scores in [0,1]
        llm_score = _composite_score(llm_hard_errors, llm_soft)
        algo_score = _composite_score(algo_hard_errors, algo_soft)

        # Bookkeeping
        total_days += 1
        sum_llm_score += llm_score
        sum_algo_score += algo_score
        if not llm_hard_errors:
            hard_valid_days_llm += 1
        if not algo_hard_errors:
            hard_valid_days_algo += 1

        # Simple diffs of event IDs
        ids_llm = [e["id"] for e in llm_sched]
        ids_algo = [e["id"] for e in algo_sched]
        missed_by_llm = [i for i in ids_algo if i not in ids_llm]
        only_in_llm = [i for i in ids_llm if i not in ids_algo]

        print(f"\n=== {client_name} @ {date_iso} ===")
        print("---- HARD CONSTRAINT CHECKS ----")
        print(f"Hard (LLM):  {'OK' if not llm_hard_errors else f'{len(llm_hard_errors)} violation(s)'}")
        if llm_hard_errors:
            for e in llm_hard_errors[:10]:
                print("  -", e)
            if len(llm_hard_errors) > 10:
                print(f"    ... and {len(llm_hard_errors) - 10} more")

        print(f"Hard (Algo): {'OK' if not algo_hard_errors else f'{len(algo_hard_errors)} violation(s)'}")
        if algo_hard_errors:
            for e in algo_hard_errors[:10]:
                print("  -", e)
            if len(algo_hard_errors) > 10:
                print(f"    ... and {len(algo_hard_errors) - 10} more")

        print("---- SCORES & STATS ----")
        print(f"Score (0–100): LLM {llm_score*100:.1f} vs Algo {algo_score*100:.1f}")
        print(f"Interest sum:   LLM {llm_soft['interest_sum']:.2f} vs Algo {algo_soft['interest_sum']:.2f}")
        print(f"Total cost:     LLM {llm_soft['total_cost']:.2f} vs Algo {algo_soft['total_cost']:.2f}")
        print(f"Utilization:    LLM {llm_soft['utilization']:.2f} vs Algo {algo_soft['utilization']:.2f}")
        print(
            "Diversity (distinct events): "
            f"LLM {llm_soft['distinct_events']} / {llm_soft['n_events']} "
            f"vs Algo {algo_soft['distinct_events']} / {algo_soft['n_events']}"
        )
        print(f"Day-window violations: LLM {llm_soft['day_window_violations']} "
              f"vs Algo {algo_soft['day_window_violations']}")

        print(f"LLM events:   {ids_llm}")
        print(f"Algo events:  {ids_algo}")
        print(f"Only in LLM:  {only_in_llm}")
        print(f"Missed vs algo: {missed_by_llm}")

    # Summary across all days
    if total_days > 0:
        avg_llm = sum_llm_score / total_days
        avg_algo = sum_algo_score / total_days
        frac_valid_llm = hard_valid_days_llm / total_days
        frac_valid_algo = hard_valid_days_algo / total_days

        print("\n=== SUMMARY OVER ALL DAYS ===")
        print(f"Days compared: {total_days}")
        print(f"Avg score (0–100): LLM {avg_llm*100:.1f} vs Algo {avg_algo*100:.1f}")
        print(
            "Hard-valid days:   "
            f"LLM {hard_valid_days_llm}/{total_days} ({frac_valid_llm:.1%}), "
            f"Algo {hard_valid_days_algo}/{total_days} ({frac_valid_algo:.1%})"
        )


if __name__ == "__main__":
    main()
