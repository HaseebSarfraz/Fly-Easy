# src/planner/core/scoring.py
from .models import Client, Activity

GAMMA_DEFAULT = 0.2    # contribution of vibe (points), we can tune this later!
VIBE_CLOSE = {
    # key vibe -> similar vibes (weight)
    "family":       {"leisurely": 0.7, "budget": 0.6, "relaxed": 0.6},
    "urban":        {"party": 0.7, "music": 0.6, "cultural": 0.5},
    "relaxed":      {"leisurely": 0.8, "family": 0.6, "cultural": 0.4},
    "cultural":     {"relaxed": 0.6, "urban": 0.5, "family": 0.4},
    "active":       {"family": 0.5, "urban": 0.4},
    "leisurely":    {"relaxed": 0.8, "family": 0.7, "cultural": 0.5},
    "party":        {"urban": 0.7, "music": 0.6},
    "music":        {"party": 0.6, "urban": 0.6},
    "budget":       {"family": 0.6, "relaxed": 0.4}
}

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


def _clamp(x, lo=0.0, hi=10.0):
    return max(lo, min(hi, x))

def norm_interest(client, act) -> float:
    """
    Return interest on a 0..10 scale.
    If your interest_score() already returns 0..10, this is just a clamp.
    """
    try:
        return _clamp(float(interest_score(client, act)))
    except Exception:
        return 0.0

def norm_popularity(act) -> float:
    """
    Popularity is 0..1 in your JSON; scale it to 0..10 to match interest.
    """
    try:
        return _clamp(float(act.popularity) * 10.0)
    except Exception:
        return 0.0
    
def _infer_vibe_tags(act: Activity) -> list[str]:
    # Prefer explicit
    if getattr(act, "vibe_tags", None):
        return [t.lower() for t in act.vibe_tags if isinstance(t, str)]

    # Fallback: derive from tags (super light heuristic)
    t = set(s.lower() for s in act.tags or [])
    derived = []
    if {"family", "kids", "zoo", "aquarium"} & t: derived.append("family")
    if {"nightlife", "bar", "club"} & t:        derived.append("party")
    if {"music", "concerts"} & t:               derived.append("music")
    if {"history", "culture", "museum"} & t:    derived.append("cultural")
    if {"outdoor", "park", "hike"} & t:         derived.append("active")
    if {"views", "walk", "free"}.issubset(t) or "indoors" in t:
        derived.append("relaxed")
    if {"shopping", "iconic", "downtown"} & t:  derived.append("urban")
    if "free" in t or "budget" in t:            derived.append("budget")
    return derived
    
def _vibe_alignment(client_vibe: str, act_vibe_tags: list[str]) -> float:
    if not client_vibe or not act_vibe_tags:
        return 0.0
    client_vibe = client_vibe.lower()
    tags = [t.lower() for t in act_vibe_tags]
    if client_vibe in tags:
        return 1.0
    close = VIBE_CLOSE.get(client_vibe, {})
    best = 0.0
    for t in tags:
        best = max(best, close.get(t, 0.0))
    return best  # 0..1

def norm_vibe(client: Client, act: Activity) -> float:
    return _vibe_alignment(getattr(client, "vibe", None), _infer_vibe_tags(act))

def base_value(client, act, alpha: float = 0.6, beta: float = 0.2, gamma: float = GAMMA_DEFAULT) -> float:
    """
    All components are 0..1. We only renormalize weights, not scales.
    """
    total = max(1e-9, alpha + beta + gamma)
    a, b, g = alpha/total, beta/total, gamma/total
    return (
        a * norm_interest(client, act) +
        b * norm_popularity(act) +
        g * norm_vibe(client, act)
    )