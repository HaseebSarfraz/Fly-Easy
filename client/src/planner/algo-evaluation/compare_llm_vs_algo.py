#!/usr/bin/env python3
import json, sys
from datetime import datetime, date, timedelta
from collections import defaultdict

from planner.core.utils import load_people, load_events
from planner.core.solver import make_day_plan
from planner.core.solver import is_weather_suitable
from planner.core.scoring import interest_score, base_value

def _minutes(s):  # "YYYY-MM-DDTHH:MM" -> minutes from midnight
    t = datetime.fromisoformat(s)
    return t.hour*60 + t.minute

def _overlap(a_start, a_dur, b_start, b_dur):
    a1, a2 = a_start, a_start + a_dur
    b1, b2 = b_start, b_start + b_dur
    return not (a2 <= b1 or b2 <= a1)

def _spent(plan):
    return sum(ev["cost_cad"] for ev in plan)

def _index_events_by_id(events):
    return {e.id: e for e in events}

def _plan_from_algo(client, events, day):
    pd = make_day_plan(client, events, day)
    out = []
    for ev in pd.events:
        out.append({
            "id": ev.activity.id,
            "start": ev.start_dt.strftime("%Y-%m-%dT%H:%M"),
            "duration_min": int(ev.activity.duration_min or 0),
            "cost_cad": float(ev.activity.cost_cad or 0.0),
            "fixed": bool(ev.activity.fixed_times),
        })
    return out

def _validate_hard(client, events_by_id, date_iso, sched):
    errs = []
    # Prep client/day bounds
    lo, hi = int(client.day_start_min), int(client.day_end_min)

    # 1) No overlaps + within client window
    day_events = []
    for ev in sched:
        if ev["id"] not in events_by_id:
            errs.append(f"Unknown event id: {ev['id']}")
            continue
        e = events_by_id[ev["id"]]
        s_min = _minutes(ev["start"])
        dur = int(ev["duration_min"])
        if not (lo <= s_min and s_min+dur <= hi):
            errs.append(f"Outside client day window: {ev['id']} @ {ev['start']} dur={dur}")
        day_events.append((s_min, dur, ev, e))
    for i in range(len(day_events)):
        for j in range(i+1, len(day_events)):
            if _overlap(day_events[i][0], day_events[i][1],
                        day_events[j][0], day_events[j][1]):
                errs.append(f"Overlap: {day_events[i][2]['id']} vs {day_events[j][2]['id']}")

    # 2) Age bounds and opening hours (approx: require start>=open_start and end<=open_end if daily set)
    for s_min, dur, evj, e in day_events:
        # age
        amin, amax = int(getattr(e, "age_min", 0) or 0), int(getattr(e, "age_max", 120) or 120)
        # party ages (your schema stores names; assume Client has adults_ages/kids_ages or travellers)
        ages=[]
        ages+=getattr(client, "adults_ages",[]) or []
        ages+=getattr(client, "kids_ages",[]) or []
        # fallback: single age
        if not ages and hasattr(client, "age"): ages=[int(client.age)]
        for a in ages:
            if not (amin <= a <= amax):
                errs.append(f"Age bound violated for {evj['id']} (age {a} not in [{amin},{amax}])")
                break

        # opening hours simple check (daily window)
        oh = getattr(e, "opening_hours", None) or {}
        daily = oh.get("daily")
        if isinstance(daily, (list, tuple)) and len(daily)==2:
            open_s = int(daily[0].split(":")[0])*60 + int(daily[0].split(":")[1])
            open_e = int(daily[1].split(":")[0])*60 + int(daily[1].split(":")[1])
            if not (open_s <= s_min and s_min+dur <= open_e):
                errs.append(f"Opening hours violated for {evj['id']}")

        # weather blockers (best-effort: reuse solver check at the scheduled time)
        # NOTE: needs activity.location + city populated properly
        # Skips check if metadata is missing.
        try:
            # Construct a datetime for the provided date at start minutes
            y,m,d = map(int, date_iso.split("-"))
            start_dt = datetime(y,m,d) + timedelta(minutes=s_min)
            # Calls your forecast-based gate
            ok = is_weather_suitable(e, start_dt)
            if not ok:
                errs.append(f"Weather blocked: {evj['id']}")
        except Exception:
            pass

        # fixed-time anchors must start at one of the declared fixed times (if present)
        ft = getattr(e, "fixed_times", None)
        if ft:
            # accept "HH:MM" or "YYYY-MM-DD HH:MM" or dict {"date":...,"start":...}
            accepted = False
            def _to_min(hm):
                hh, mm = map(int, hm.split(":"))
                return hh*60+mm
            if isinstance(ft, list):
                for item in ft:
                    if isinstance(item, str):
                        hm = item.strip().split()[-1]  # get rightmost time
                        if _to_min(hm)==s_min: accepted=True
                    elif isinstance(item, dict) and "start" in item:
                        if _to_min(item["start"])==s_min: accepted=True
            elif isinstance(ft, dict) and "start" in ft:
                if _to_min(ft["start"])==s_min: accepted=True
            elif isinstance(ft,str):
                hm = ft.strip().split()[-1]
                if _to_min(hm)==s_min: accepted=True
            if not accepted:
                errs.append(f"Fixed-time violation: {evj['id']} @ {evj['start']}")
    return errs

def main():
    if len(sys.argv)<2:
        print("Usage: python scripts/compare_llm_vs_algo.py llm_plans.json")
        sys.exit(1)

    llm_json = json.load(open(sys.argv[1], "r", encoding="utf-8"))
    plans = llm_json.get("plans", [])

    people = load_people()
    events = load_events()
    events_by_id = _index_events_by_id(events)
    people_by_name = {getattr(p,"name","Client"): p for p in people}

    # Group LLM plans by (client,date)
    llm_map = defaultdict(list)
    for entry in plans:
        llm_map[(entry["client"], entry["date"])] = entry["events"]

    # For each (client,date) in LLM output, build our algo plan and compare
    for (client_name, date_iso), llm_sched in llm_map.items():
        client = people_by_name.get(client_name) or people[0]
        y,m,d = map(int, date_iso.split("-"))
        algo_sched = _plan_from_algo(client, events, date(y,m,d))

        # Validate LLM hard constraints
        hard_errors = _validate_hard(client, events_by_id, date_iso, llm_sched)
        ok = "OK" if not hard_errors else f"{len(hard_errors)} HARD VIOLATION(S)"

        # Simple diffs
        ids_llm = [e["id"] for e in llm_sched]
        ids_algo = [e["id"] for e in algo_sched]
        missed_by_llm = [i for i in ids_algo if i not in ids_llm]
        only_in_llm   = [i for i in ids_llm if i not in ids_algo]

        spent_llm = sum(float(events_by_id[i]["cost_cad"] if isinstance(events_by_id[i],dict) else events_by_id[i].cost_cad)
                        for i in ids_llm if i in events_by_id)
        spent_algo = sum(e["cost_cad"] for e in algo_sched)

        print(f"\n=== {client_name} @ {date_iso} ===")
        print(f"Hard-constraints: {ok}")
        if hard_errors:
            for e in hard_errors[:10]:
                print(" -", e)
            if len(hard_errors)>10:
                print(f"   ... and {len(hard_errors)-10} more")

        print(f"LLM events:  {ids_llm}")
        print(f"Algo events: {ids_algo}")
        print(f"Only in LLM: {only_in_llm}")
        print(f"Missed vs algo: {missed_by_llm}")
        print(f"Spend LLM vs Algo: {spent_llm:.2f} vs {spent_algo:.2f}")

if __name__ == "__main__":
    main()
