# src/planner/core/scoring.py
from .models import Client, Activity


def interest_score(client: Client, act: Activity) -> float:
    """
    Simple soft score in [0, ~10+]. Sums client's weights for tags on the activity,
    then adds a small popularity bonus.

    If client likes ["food":7, "museum":5] and activity has tags ["food","indoor"], tag_sum = 7.

    Popularity 0.87 → +1.74 bonus.

    """
    tag_sum = 0
    for tag in act.tags: 
        tag_sum += client.interest(tag)

    pop_bonus = act.popularity * 2.0    # slight nudge for popularity of the acitivity
    return float(tag_sum) + pop_bonus