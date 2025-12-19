# src/planner/core/scoring.py
import math
from planner.core.models import Client, Activity, Location

# TODO: BALANCING TASK -> OVER THE TRIP, YOU SATISFY EACH PERSON'S NEEDS ATLEAST ONCE
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


def _vibe_bonus(client: Client, act: Activity, gamma: float = GAMMA_DEFAULT) -> float:
    """
    Small bonus based on how well the activity's vibe matches the client's vibe.
    Uses VIBE_CLOSE table + exact matches on act.vibe_tags if present.
    """
    client_vibe = (getattr(client, "vibe", "") or "").lower().strip()
    if not client_vibe:
        return 0.0

    close = VIBE_CLOSE.get(client_vibe, {})
    tags = getattr(act, "vibe_tags", None) or getattr(act, "tags", []) or []

    score = 0.0
    for t in tags:
        vt = (t or "").lower().strip()
        if vt == client_vibe:
            score += 1.0
        else:
            score += close.get(vt, 0.0)

    # Damp + cap so vibe doesn't dominate interest
    return gamma * min(score, 3.0)


def base_value(client: Client, act: Activity) -> float:
    """
    Core utility score for an activity, used by the greedy planner.

    Right now:
      - starts from interest_score (group satisfaction)
      - adds a small vibe bonus based on client.vibe & act.vibe_tags/tags
    Budget effects are handled separately in the planner (LAMBDA_BUDGET, etc.).
    """
    i_score, _, _ = interest_score(client, act)   # ~0–10+
    v_bonus = _vibe_bonus(client, act)            # usually 0–0.6-ish

    return float(i_score + v_bonus)

