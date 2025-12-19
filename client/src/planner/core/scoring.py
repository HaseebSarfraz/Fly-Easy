# src/planner/core/scoring.py
import math
from planner.core.models import Client, Activity, Location

MAX_CREDS_PER_MEMBER = 2  # MAX CREDITS ALLOWED PER MEMBER FOR AN EXTREME ACCOMMODATION
HOURS_PER_CREDIT = 2  # EACH CREDIT CAN BE USED FOR A 2-HOUR ACCOMMODATION
EXTREME_INTEREST_MIN_SCORE = 8.5  # MINIMUM SCORE FOR SOMEONE TO BE CONSIDERED "EXTREMELY INTERESTED"
PENALTY_SENSITIVITY = 0.4  # USED FOR CONTROLLING SENSITIVITY OF PENALIZATION FOR TIME DISTRIBUTION
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


def interest_score(client: Client, act: Activity) -> tuple[float, dict, dict]:
    """
    Soft score for an activity [0, 10+]. Sums client's interest weights on an activity.
    This modified version accounts for extreme interest cases, so if this activity satisfies a member
    who is extremely interested but not as such for others, it might give it a high score depending on whether
    that person can be given the accommodation or not.

    === IMPORTANT INFO ON "CREDITS" ===
    We use a "credit" system which means that each family member has a chance to attend an event of their choice
    if they are extremely interested compared to the other members. Each "credit" can be used for up to a 2-hour block
    as well. But there is a limit on the number of credits a member can use for this event: 2. If multiple
    members are in this situation then their credits will also be used up. If there are not enough credits then
    this "extreme interest" event is not added to the planner.
    """
    activity_hrs = act.duration_min / 60
    creds_required = math.ceil(activity_hrs / 2)  # NUMBER OF CREDITS REQUIRED FOR EXTREME ACCOMODATION
    interest_scores = {}  # INTEREST SCORES OF THE ENTIRE FAMILY
    not_ext_interested = []  # LIST OF ALL "NOT EXTREMELY INTERESTED" SCORES
    ext_interested = []  # LIST OF ALL "EXTREMELY INTERESTED" SCORES
    ext_interested_creds = {}  # DICTIONARY OF CREDITS USED BY EACH EXTREMELY INTERESTED MEMBER
    num_members = len(client.party_members)  # THE NUMBER OF MEMBERS IN THE PARTY (FAMILY)

    for member in client.party_members:  # ITERATES OVER EACH MEMBER IN THE FAMILY
        member_interest = 0  # THE INTEREST SCORE OF THIS MEMBER
        for tag in act.tags:  # ITERATES OVER THE ACTIVITY "TAGS", USED FOR CALCULATING THE INTEREST SCORE OF THIS MEMBER
            # THE LINE BELOW INCREASES THIS MEMBER'S INTEREST SCORE BASED ON THE CURRENT TAG'S INTEREST AND AGE SCORE
            member_interest += client.interest(tag, member)
        interest_scores[member] = member_interest  # STORES THIS MEMBER'S OVERALL INTEREST SCORE FOR THIS EVENT
        if member_interest >= EXTREME_INTEREST_MIN_SCORE:  # LIST OF SCORES FOR THOSE EXTREMELY INTERESTED
            ext_interested.append(member_interest)  # IF THE MEMBER HAS A HIGH INTEREST SCORE, ADD THEM TO THIS LIST
            # ext_interested_creds[member] = client.credits_left[member]  # STORE THIS PERSON'S "ACCOMOCATION" CREDITS
            ext_interested_creds[member] = 0
        else:  # LIST OF SCORES FOR THOSE NOT EXTREMELY INTERESTED (INTEREST SCORE COULD STILL BE HIGH)
            not_ext_interested.append(member_interest)  # NOT-SUPER-INTERESTED MEMBERS GET ADDED HERE
    average_interest_score = sum(interest_scores.values()) / num_members  # AVERAGE SUITABILITY SCORE FOR THE GROUP

    total_ext_score, total_ext_count = sum(ext_interested), len(ext_interested)  # SUM AND NUMBER OF THE INTEREST SCORES
    total_not_ext_score, total_not_ext_count = sum(not_ext_interested), len(
        not_ext_interested)  # SAME AS ABOVE BUT FOR THE NOT-SUPER-INTERESTED

    # ======= OPTIMIZATION MEASURE: IF THE ENTIRE FAMILY IS IN THE SAME INTEREST GROUP THEN WE RETURN THE
    # AVERAGE INTEREST SCORE. =======
    if total_ext_count == 0 or total_not_ext_count == 0:
        return average_interest_score, {}, interest_scores

    ext_interested_avg = sum(ext_interested) / len(ext_interested)  # AVG SCORE OF EXTREMELY INTERESTED
    not_ext_interested_avg = sum(not_ext_interested) / len(not_ext_interested)  # AVG SCORE OF NOT EXTREMELY INTERESTED

    interest_score_diff = ext_interested_avg - not_ext_interested_avg  # THIS WILL ALWAYS BE POSITIVE
    extreme_score = 0  # SCORE FOR THE EXTREME ACCOMMODATION SCENARIO. IF NO EXTREME ACCOMMODATION, SCORE IS 0.

    # THE SORTED LIST'S PURPOSE IS TO DEDUCT CREDITS FROM THOSE WHO ARE MOST INTERESTED FIRST
    ext_interest_sorted = sorted(  # WE SORT THE NAMES OF MEMBERS BASED ON THEIR INTEREST SCORE IN DESCENDING ORDER
        ext_interested_creds.keys(),
        key=lambda m: interest_scores[m],
        reverse=True
    )

    if interest_score_diff >= 3:  # CHECKS IF THE INTEREST SCORE IS SIGNIFICANT ENOUGH FOR ANY EXTREME ACCOMMODATION
        extreme_score = max(interest_scores.values())  # TAKES THE ABSOLUTE MAXIMUM INTEREST SCORE
        i = 0
        while creds_required > 0 and i < len(ext_interest_sorted):
            creds_2 = creds_required - 2
            use_creds = int(creds_2 >= 0) + 1  # USE 2 CREDITS IF THE REQUIRED NUMBER OF CREDITS AFTER UPDATE IS >= 0
            ext_interested_creds[ext_interest_sorted[i]] = use_creds
            creds_required -= use_creds
            i += 1
    if creds_required == 0 and extreme_score > average_interest_score:  # EVERYONE IN THE GROUP HAS ENOUGH CREDITS TO DO THIS
        return extreme_score, ext_interested_creds, interest_scores  # RETURN THE MAX SCORE
    else:  # OTHERWISE IF THERE IS NOT ENOUGH CREDITS LEFT THEN WE CONSIDER THIS A REGULAR EVENT
        return average_interest_score, {}, interest_scores


# FIRST PENALTY APPLIED IN INITIAL SCORING
def duration_penalty(act: Activity, client: Client, avg_interest_score: float, gamma: float = 1.2) -> float:
    base = max(0, math.ceil(1 - avg_interest_score / 10))  # ensure non-negative
    dur_pen = (act.duration_min / client.total_day_duration) * (base ** gamma)
    return min(10, dur_pen * 10)


# SECOND SET OF PENALTIES APPLIED AFTER SECOND WAVE OF PLANNING
def conflict_penalty(act: Activity, client: Client, tags_count: dict[str, int],
                      gamma: float = 1.1) -> float:
    """
    Penalizes each individual activity based on the number of conflicts with earlier, more-popular activities.
    """
    conf_pen = 0
    for tag in act.tags:
        times_repeated = tags_count.get(tag, 0)  # how many times this tag has appeared already
        average_interest_wgt = (
                sum([m["interest_weights"].get(tag, 0) for m in client.party_members.values()])
                / (len(client.party_members) * 10)
        )
        interest_factor = 1 - average_interest_wgt
        act_duration_share = act.duration_min / client.total_day_duration

        conf_pen += times_repeated * (interest_factor ** gamma) * (1 + act_duration_share)
    # final sort by adjusted score
    return min(conf_pen * 10, 10)


if __name__ == "__main__":
    from datetime import datetime

    # -----------------------------
    # Define client (extreme-interest case)
    # -----------------------------
    client_data = {
        "id": "family_extreme_interest_01",
        "party_type": "family",
        "party_members": {
            "Parent 1": {"age": 47, "interest_weights": {"theme_parks": 10}},
            "Parent 2": {"age": 38, "interest_weights": {"theme_parks": 0}},
            "Child 1": {"age": 12, "interest_weights": {"theme_parks": 0}},
            "Child 2": {"age": 8, "interest_weights": {"theme_parks": 0}},
        },
        "religion": "none",
        "ethnicity_culture": ["generic"],
        "vibe": "family-fun",
        "budget_total": 500,
        "trip_start": "2026-08-01",
        "trip_end": "2026-08-25",
        "home_base": {"lat": 43.65, "lng": -79.38},
        "avoid_long_transit": 5,
        "prefer_outdoor": 7,
        "prefer_cultural": 3,
        "day_start_time": "08:00",
        "day_end_time": "20:00",
    }

    client_data["trip_start"] = datetime.strptime(client_data["trip_start"], "%Y-%m-%d").date()
    client_data["trip_end"] = datetime.strptime(client_data["trip_end"], "%Y-%m-%d").date()

    client = Client(**client_data)
    client.total_day_duration = 12 * 60  # 12-hour day

    # -----------------------------
    # Define activities (same tag!)
    # -----------------------------
    activities = [
        Activity(
            id="a1",
            name="Mega Theme Park",
            category="theme_parks",
            tags=["theme_parks"],
            venue="Wonderland",
            city="Toronto",
            location=Location(43.64, -79.38, "Toronto"),
            duration_min=180,
            cost_cad=80,
            age_min=5,
            age_max=99,
            opening_hours={},
            fixed_times=[],
            requires_booking=True,
            weather_blockers=[],
            popularity=0.9,
        ),
        Activity(
            id="a2",
            name="Smaller Theme Park",
            category="theme_parks",
            tags=["theme_parks"],
            venue="FunLand",
            city="Toronto",
            location=Location(43.66, -79.4, "Toronto"),
            duration_min=120,
            cost_cad=50,
            age_min=5,
            age_max=99,
            opening_hours={},
            fixed_times=[],
            requires_booking=False,
            weather_blockers=[],
            popularity=0.6,
        ),
        Activity(
            id="a3",
            name="Theme Park Parade",
            category="theme_parks",
            tags=["theme_parks"],
            venue="Downtown",
            city="Toronto",
            location=Location(43.65, -79.37, "Toronto"),
            duration_min=60,
            cost_cad=0,
            age_min=0,
            age_max=99,
            opening_hours={},
            fixed_times=[],
            requires_booking=False,
            weather_blockers=[],
            popularity=0.4,
        ),
    ]

    # -----------------------------
    # Apply conflict penalty sequentially
    # -----------------------------
    tags_count = {}

    print("\n=== Conflict Penalty Test (Sequential) ===\n")

    for idx, act in enumerate(activities, start=1):
        conf_pen = conflict_penalty(act, client, tags_count)
        print(f"{idx}. {act.name}")
        print(f"   Tags so far: {tags_count}")
        print(f"   Conflict penalty applied: {conf_pen:.4f}\n")
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
