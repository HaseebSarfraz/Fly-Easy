import itertools
from datetime import timedelta

# Import core objects from your project
# Ensure these import paths match your directory structure
from planner.core.optimized_greedy import (
    make_day_plan,
    PlannerConfig,
    _to_minutes,
    _meal_window,
    _soft_cap_per_day,
)
from planner.core.scoring import interest_score
from planner.core.utils import *


def evaluate_configuration(client, activities, config):
    """
    Generates a multi-day plan and calculates violation scores for 6 soft constraints.
    """
    plans = []
    current_date = client.trip_start

    # Generate the plan day-by-day to ensure the Config is applied
    while current_date <= client.trip_end:
        day_plan = make_day_plan(client, activities, current_date, config=config)
        plans.append(day_plan)
        current_date += timedelta(days=1)

    daily_budget_cap = _soft_cap_per_day(client)
    total_violations = 0
    results_breakdown = []

    for i, plan_day in enumerate(plans):
        day_stats = {
            "day": i + 1,
            "window_v": 0,  # Day Window
            "anchor_v": 0,  # Meal Anchor Conflict
            "satisfy_v": 0,  # Group Satisfaction
            "budget_v": 0,  # Budget Over-cap
            "meal_win_v": 0,  # Meal Pref Window
            "nudge_v": 0  # RepairB Nudges
        }

        # Identify fixed activities (Anchors) for the day
        anchors = [ev for ev in plan_day.events if getattr(ev.activity, "fixed_times", None)]

        # 4. Budget Check (Soft Cap)
        daily_cost = sum(ev.activity.cost_cad for ev in plan_day.events)
        if daily_cost > daily_budget_cap:
            day_stats["budget_v"] = daily_cost - daily_budget_cap

        for ev in plan_day.events:
            act = ev.activity
            start_m = _to_minutes(ev.start_dt.strftime("%H:%M"))
            end_m = start_m + act.duration_min

            # 1. Day Window Violation
            if start_m < client.day_start_min or end_m > client.day_end_min:
                day_stats["window_v"] += 1

            # 2 & 5. Meal Logic
            if act.category == "food":
                # 2. Meal vs Anchor Conflict
                for anchor in anchors:
                    a_start = _to_minutes(anchor.start_dt.strftime("%H:%M"))
                    a_end = a_start + anchor.activity.duration_min
                    if not (end_m <= a_start or start_m >= a_end):
                        day_stats["anchor_v"] += 1

                # 5. Preferred Meal Window
                # Attempts to match 'breakfast', 'lunch', or 'dinner' from activity ID
                for m_type in ["breakfast", "lunch", "dinner"]:
                    if m_type in act.id.lower():
                        try:
                            s_pref, e_pref = _meal_window(client, m_type)
                            if start_m < _to_minutes(s_pref) or start_m > _to_minutes(e_pref):
                                day_stats["meal_win_v"] += 1
                        except KeyError:
                            pass

            # 3. Group Satisfaction (<50% interest)
            # uses the interest_score helper from your core/scoring.py
            _, _, indiv_scores = interest_score(client, act)
            if indiv_scores:
                interested_count = sum(1 for s in indiv_scores.values() if s > 0)
                if interested_count < (len(client.party_members) / 2):
                    day_stats["satisfy_v"] += 1

            # 6. Minimal Nudging (Repair B)
            # Checks if the activity was modified during RepairB via tags
            if any("note:" in str(tag).lower() for tag in getattr(act, "tags", [])):
                day_stats["nudge_v"] += 1

        # Calculate weighted day score (Lower is better)
        day_score = (
                (day_stats["window_v"] * 15) +
                (day_stats["anchor_v"] * 20) +
                (day_stats["satisfy_v"] * 10) +
                (day_stats["budget_v"] * 0.05) +
                (day_stats["meal_win_v"] * 10) +
                (day_stats["nudge_v"] * 5)
        )
        day_stats["total"] = day_score
        results_breakdown.append(day_stats)
        total_violations += day_score

    return total_violations / len(plans), results_breakdown


def run_16_combination_test(client, activities):
    """
    Runs all 16 permutations of the PlannerConfig toggles.
    """
    options = [True, False]
    # use_budget, use_meals, use_base_plan, use_repairB
    combinations = list(itertools.product(options, repeat=4))

    summary = []

    print(f"--- Running Planner Evaluation (16 Configs) ---")

    for b, m, base, rB in combinations:
        cfg = PlannerConfig(
            use_weather=False,  # Constant as requested
            use_budget=b,
            use_meals=m,
            use_base_plan=base,
            use_repairB=rB,
            debug_print=False
        )

        avg_score, details = evaluate_configuration(client, activities, cfg)

        summary.append({
            "score": avg_score,
            "config": f"Budget:{b} | Meal planning:{m} | Making base plan:{base} | Using RepairB:{rB}",
            "details": details
        })

    # Sort results to find the best configuration
    summary.sort(key=lambda x: x["score"])

    # Output formatted report
    print("=" * 70)
    print(f"{'RANK':<5} | {'AVG VIOLATION SCORE':<20} | {'CONFIGURATION'}")
    print("-" * 70)
    for i, res in enumerate(summary):
        print(f"#{i + 1:02}   | {res['score']:<20.2f} | {res['config']}")
    print("=" * 70, "\n")

# --- Usage ---
# SIDE NOTE: FOR CLEANER OUTPUTS, COMMENT OUT LINE 360 INSIDE PLANNER/CORE/OPTIMIZED_GREEDY.PY LINE 360
clients = load_people()
for c in range(len(clients)):
    print(f"RUNNING THE 16 TOGGLE CONFIGURATIONS ON CLIENT {c + 1}")
    run_16_combination_test(clients[c], load_events())
