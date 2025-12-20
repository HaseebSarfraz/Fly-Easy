# src/planner/core/energy.py
from typing import Dict, Optional
from .models import Activity, Client

# Energy thresholds
MIN_ENERGY_FOR_HIGH_ACTIVITY = 30.0
MIN_ENERGY_FOR_MEDIUM_ACTIVITY = 15.0
ENERGY_RESTORE_PER_DAY = 80.0
MAX_ENERGY = 100.0

# Activity categories mapped to energy costs (0-100 scale)
ENERGY_COST_BY_CATEGORY = {
    "walk": 15,
    "hike": 40,
    "sports": 50,
    "active": 45,
    "outdoor": 25,
    "museum": 10,
    "art": 8,
    "culture": 12,
    "viewpoint": 5,
    "attraction": 15,
    "aquarium": 12,
    "concert": 20,
    "theater": 15,
    "shopping": 20,
    "food": 5,
    "relaxation": 3,
    "spa": 2,
    "beach": 15,
    "park": 10,
}

HIGH_ENERGY_TAGS = {
    "hiking", "running", "cycling", "swimming", "sports", "active", 
    "adventure", "extreme", "fitness", "workout", "athletic"
}

LOW_ENERGY_TAGS = {
    "relaxed", "leisurely", "indoors", "sitting", "viewing", "watching",
    "spa", "massage", "meditation", "quiet", "calm"
}


def calculate_activity_energy_cost(activity: Activity) -> float:
    """
    Calculate the energy cost of an activity based on its category, tags, and duration.
    Returns a value between 0-100 representing energy cost.
    """
    if hasattr(activity, 'energy_level') and activity.energy_level is not None:
        return float(activity.energy_level)

    category = activity.category.lower() if activity.category else ""
    base_cost = ENERGY_COST_BY_CATEGORY.get(category, 15)

    tags_lower = {tag.lower() for tag in (activity.tags or [])}

    if any(tag in HIGH_ENERGY_TAGS for tag in tags_lower):
        base_cost = min(100, base_cost + 25)

    if any(tag in LOW_ENERGY_TAGS for tag in tags_lower):
        base_cost = max(0, base_cost - 10)
    duration_factor = activity.duration_min / 60.0
    base_cost = base_cost * duration_factor

    return max(0.0, min(100.0, base_cost))


def get_activity_energy_level(activity: Activity) -> str:
    """
    Classify activity energy level as "low", "medium", or "high".
    """
    cost = calculate_activity_energy_cost(activity)
    if cost < 15:
        return "low"
    elif cost < 35:
        return "medium"
    else:
        return "high"


def has_sufficient_energy(client: Client, activity: Activity) -> bool:
    """
    Check if the family has sufficient energy for an activity.
    For families, we check the minimum energy across all members.
    """
    if not hasattr(client, 'energy_levels') or not client.energy_levels:
        return True
    min_energy = min(client.energy_levels.values()) if client.energy_levels else 100.0

    energy_level = get_activity_energy_level(activity)

    if energy_level == "high":
        return min_energy >= MIN_ENERGY_FOR_HIGH_ACTIVITY
    elif energy_level == "medium":
        return min_energy >= MIN_ENERGY_FOR_MEDIUM_ACTIVITY
    else:
        return min_energy >= 0


def deduct_energy(client: Client, activity: Activity) -> None:
    """
    Deduct energy from all family members after completing an activity.
    """
    if not hasattr(client, 'energy_levels') or not client.energy_levels:
        return

    energy_cost = calculate_activity_energy_cost(activity)

    for name in client.energy_levels:
        client.energy_levels[name] = max(0.0, client.energy_levels[name] - energy_cost)


def restore_energy(client: Client, restore_amount: Optional[float] = None) -> None:
    """
    Restore energy for all family members (e.g., after a night's rest).
    """
    if not hasattr(client, 'energy_levels') or not client.energy_levels:
        return
    restore = restore_amount if restore_amount is not None else ENERGY_RESTORE_PER_DAY
    for name in client.energy_levels:
        client.energy_levels[name] = min(MAX_ENERGY, client.energy_levels[name] + restore)


def get_family_energy_status(client: Client) -> Dict[str, float]:
    """
    Get current energy levels for all family members.
    """
    if not hasattr(client, 'energy_levels') or not client.energy_levels:
        return {}
    return dict(client.energy_levels)


def get_min_family_energy(client: Client) -> float:
    """
    Get the minimum energy level across all family members.
    Useful for determining if family is too tired for activities.
    """
    if not hasattr(client, 'energy_levels') or not client.energy_levels:
        return 100.0
    return min(client.energy_levels.values()) if client.energy_levels else 100.0
