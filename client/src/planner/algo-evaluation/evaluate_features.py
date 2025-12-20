#!/usr/bin/env python3

from datetime import timedelta
from pathlib import Path
import sys
import io
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).parent.parent))

from ..core.utils import load_people, load_events
from ..core.optimized_greedy import make_day_plan, PlannerConfig


def print_plan_summary(client, plan, day_idx, seen_activities):
    """Prints activities chosen for the day and checks for duplicates across days."""
    print(f"\nDay {day_idx + 1}:")
    activities_today = []

    for event in plan.events:
        activity_id = event.activity.id
        activities_today.append(activity_id)
        if activity_id in seen_activities:
            print(f"  WARNING: Duplicate activity detected: {activity_id}")
        else:
            seen_activities.add(activity_id)
        print(f"    - {activity_id}")

    print(f"  Total activities today: {len(activities_today)}")


def main():
    print("\n=== FEATURE EVALUATION (DUPLICATE CHECK ONLY) ===")

    people = load_people()
    events = load_events()

    client = people[0]
    test_events = events[:20]

    config = PlannerConfig(
        use_energy=False,  # ignore energy
        use_meals=True,
        use_budget=False,
        debug_print=False,
    )

    day = client.trip_start
    days = (client.trip_end - client.trip_start).days + 1

    seen_activities = set()

    for day_idx in range(days):
        # suppress all internal planner prints
        silent = io.StringIO()
        with redirect_stdout(silent):
            plan = make_day_plan(client, test_events, day, config=config)

        print_plan_summary(client, plan, day_idx, seen_activities)
        day += timedelta(days=1)

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()
