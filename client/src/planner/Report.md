# Fly-Easy Day Planner — Constraints & Budget Logic

_Last updated: 2025-11-21_

## 1) Overview
The planner builds a single-day itinerary that **must** satisfy hard constraints (age, opening hours/fixed times, no overlaps, weather) and **should** optimize soft preferences (interest/popularity) while respecting a **soft daily budget cap** with penalties when exceeded.

---

## 2) Inputs & Data Model
- **Client**
  - Interests/preferences, party ages, `trip_start` / `trip_end`, `budget_total`.
- **Activity**
  - `duration_min`, `cost_cad`, `opening_hours`, optional `fixed_times`,
    `age_min`/`age_max`, `weather_blockers`, `popularity`, `city`, `location(lat,lng)`.
- **Time Grid**
  - Candidate starts from `generate_candidate_times(...)` with step from `choose_step_minutes(...)`.

---

## 3) Hard Constraints (must pass)
### 3.1 Age restriction
- **Checker**: `hc_age_ok(...)` via `hard_feasible(...)`  
- **Rule**: every attendee age ∈ \[`age_min`, `age_max`].

### 3.2 Open window / schedule feasibility
- **Checker**: `hc_open_window_ok(...)` via `hard_feasible(...)`  
- **Rule**: `start_dt + duration` must lie within opening hours for that weekday.  
  If `fixed_times` exists, start must match one of them.

### 3.3 No time overlap
- **Checker**: `fits_no_overlap(...)`  
- **Rule**: the interval `[start_dt, end_dt)` must not intersect any already-planned `PlanEvent`.

### 3.4 Weather suitability (treated as **hard**)
- **Checker**: `is_weather_suitable(...)` using Open-Meteo hourly `weathercode → label → blockers`.  
- **Rule**: if any label in `[start_dt, end_dt]` appears in `activity.weather_blockers`, **reject**.

### 3.5 Minimal repair (nudge) when overlapping
- **Procedure**: `repairB(...)`
  1) Identify **direct blocker** (max overlap minutes) and try nudging it forward up to `max_moves`.  
  2) If that fails and `try_others=True`, try other **non-fixed** events ordered by **least flexibility** (fewest feasible alternative slots).  
  - **Rollback safety**: take a snapshot of all event start/end times. If later **budget gate** fails, pop the just-added event and restore the snapshot.

---

## 4) Soft Constraints (scored & budget-aware)
### 4.1 Pre-ordering by desirability
- Sort activities by `base_value(client, act)` (encodes interests + popularity) **before** considering budget penalty.

### 4.2 Daily budget soft cap
```text
days_in_trip = max(1, (trip_end - trip_start).days + 1)
soft_cap_day = budget_total / days_in_trip.


### 4.3 Daily budget soft cap
```text
spent_today = sum(cost of events already placed)

# When evaluating BEFORE adding (no-overlap path):
over    = max(0, spent_today + act.cost_cad - soft_cap_day)

# When evaluating AFTER a tentative repair add:
over    = max(0, spent_today - soft_cap_day)   # act already counted

penalty = LAMBDA_BUDGET * over        # $ → points, e.g., 0.03 pts per $1
net     = base_value(client, act) - penalty

### 4.4 Acceptance rule

 - If over == 0 → accept (passes soft cap).

 - If over > 0 → accept only if net ≥ SCORE_THRESHOLD (e.g., 0.10).

## 5) Candidate generation logic
- For each activity (sorted by base_value), iterate candidate starts from generate_candidate_times(act, day, step_minutes=choose_step_minutes(act) or 60).

## 6) Event selection algorithm (greedy + repair + budget gate)

1. iterate activities in descending base_value.

2. For each candidate start:

- Check hard constraints (age, window/fixed, weather).

- If no overlap:

    - Compute over and net (Section 4.3) and apply Acceptance rule (4.4).

    - If accepted → plan.add(...) and break to next activity.

- If overlap:

     - Take snapshot; run repairB(...).

     - If placed, compute net with already_added=True.

        - If accepted → keep; else pop & rollback and try next start.

3. After all, sort events chronologically.

## 7) Tunable parameters

- LAMBDA_BUDGET (default 0.03): penalty slope ($ → points).

- SCORE_THRESHOLD (default 0.10): minimum net to accept once over budget.

- max_moves in repairB (default 1): nudge depth.

- choose_step_minutes(...): candidate grid density.