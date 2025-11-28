# src/planner/core/scoring.py
import math
from planner.core.models import Client, Activity
from datetime import datetime

MAX_CREDS_PER_MEMBER = 2  # MAX CREDITS ALLOWED PER MEMBER FOR AN EXTREME ACCOMMODATION
HOURS_PER_CREDIT = 2      # EACH CREDIT CAN BE USED FOR A 2-HOUR ACCOMMODATION
EXTREME_INTEREST_MIN_SCORE = 8.5  # MINIMUM SCORE FOR SOMEONE TO BE CONSIDERED "EXTREMELY INTERESTED"


def interest_score_age(client: Client, act: Activity) -> float:
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
    interest_scores = {}                          # INTEREST SCORES OF THE ENTIRE FAMILY
    not_ext_interested = []                       # LIST OF ALL "NOT EXTREMELY INTERESTED" SCORES
    ext_interested = []                           # LIST OF ALL "EXTREMELY INTERESTED" SCORES
    ext_interested_creds = {}                     # DICTIONARY OF CREDITS FOR EACH EXTREMELY INTERESTED MEMBER
    num_members = len(client.party_members)       # THE NUMBER OF MEMBERS IN THE PARTY (FAMILY)
    for member in client.party_members:           # ITERATES OVER EACH MEMBER IN THE FAMILY
        age = client.party_members[member]["age"]  # THE AGE OF THIS MEMBER
        member_age_score = _check_age_factor(age, act)  # THE AGE SCORE OF THIS ACTIVITY TO THIS PERSON'S AGE
        member_interest = 0     # THE INTEREST SCORE OF THIS MEMBER
        for tag in act.tags:    # ITERATES OVER THE ACTIVITY "TAGS", USED FOR CALCULATING THE INTEREST SCORE OF THIS MEMBER
            # THE LINE BELOW INCREASES THIS MEMBER'S INTEREST SCORE BASED ON THE CURRENT TAG'S INTEREST AND AGE SCORE
            member_interest += client.interest(tag, member) * member_age_score
        interest_scores[member] = member_interest   # STORES THIS MEMBER'S OVERALL INTEREST SCORE FOR THIS EVENT
        if member_interest >= EXTREME_INTEREST_MIN_SCORE:  # LIST OF SCORES FOR THOSE EXTREMELY INTERESTED
            ext_interested.append(member_interest)  # IF THE MEMBER HAS A HIGH INTEREST SCORE, ADD THEM TO THIS LIST
            ext_interested_creds[member] = client.credits_left[member]  # STORE THIS PERSON'S "ACCOMOCATION" CREDITS
        else:   # LIST OF SCORES FOR THOSE NOT EXTREMELY INTERESTED (INTEREST SCORE COULD STILL BE HIGH)
            not_ext_interested.append(member_interest)  # NOT-SUPER-INTERESTED MEMBERS GET ADDED HERE
    average_interest_score = sum(interest_scores.values()) / num_members  # AVERAGE SUITABILITY SCORE FOR THE FAMILY

    total_ext_score, total_ext_count = sum(ext_interested), len(ext_interested)  # SUM AND NUMBER OF THE INTEREST SCORES
    total_not_ext_score, total_not_ext_count = sum(not_ext_interested), len(not_ext_interested) # SAME AS ABOVE BUT FOR THE NOT-SUPER-INTERESTED

    # ======= OPTIMIZATION MEASURE: IF THE ENTIRE FAMILY IS IN THE SAME INTEREST GROUP THEN WE RETURN THE
    # AVERAGE INTEREST SCORE. =======
    if total_ext_count == 0 or total_not_ext_count == 0:
        return average_interest_score

    ext_interested_avg = sum(ext_interested) / len(ext_interested)  # AVG SCORE OF EXTREMELY INTERESTED
    not_ext_interested_avg = sum(not_ext_interested) / len(not_ext_interested)  # AVG SCORE OF NOT EXTREMELY INTERESTED

    interest_score_diff = ext_interested_avg - not_ext_interested_avg  # THIS WILL ALWAYS BE POSITIVE
    extreme_score = 0  # SCORE FOR THE EXTREME ACCOMMODATION SCENARIO. IF NO EXTREME ACCOMMODATION, SCORE IS 0.

    # THE SORTED LIST'S PURPOSE IS TO DEDUCT CREDITS FROM THOSE WHO ARE MOST INTERESTED FIRST
    ext_interest_sorted = sorted(   # WE SORT THE NAMES OF MEMBERS BASED ON THEIR INTEREST SCORE IN DESCENDING ORDER
        ext_interested_creds.keys(),
        key=lambda m: interest_scores[m],
        reverse=True
    )

    if interest_score_diff >= 3:    # CHECKS IF THE INTEREST SCORE IS SIGNIFICANT ENOUGH FOR ANY EXTREME ACCOMMODATION
        extreme_score = max(interest_scores.values())   # TAKES THE ABSOLUTE MAXIMUM INTEREST SCORE
        for i in ext_interest_sorted:   # GOES OVER ALL THE EXTREMELY INTERESTED MEMBER
            if creds_required >= MAX_CREDS_PER_MEMBER:  # CHECKS IF THERE ARE AT LEAST 2 CREDITS NEEDED FOR THIS EVENT
                if ext_interested_creds[i] >= MAX_CREDS_PER_MEMBER:  # PERSON HAS AT LEAST 2 CREDITS
                    ext_interested_creds[i] -= 2
                    creds_required -= 2
                    if creds_required == 0:
                        break
                elif ext_interested_creds[i] == 1:  # PERSON HAS 1 CREDIT LEFT
                    ext_interested_creds[i] -= 1
                    creds_required -= 1
                else:                               # PERSON HAS NO CREDITS
                    continue
            elif creds_required == 1:
                if ext_interested_creds[i] > 0:
                    ext_interested_creds[i] -= 1
                    creds_required = 0
                    break
                else:
                    continue
            else:   # SOMEHOW NO EXTREME ACCOMMODATION IS NEEDED (THIS SHOULD IDEALLY NOT HAPPEN)
                break

    if creds_required == 0:  # EVERYONE IN THE GROUP HAS ENOUGH CREDITS TO DO THIS
        if extreme_score > average_interest_score:
            for i in ext_interested_creds:
                client.credits_left[i] = ext_interested_creds[i]    # UPDATE THE CREDITS FOR EACH INTERESTED MEMBER
        return extreme_score    # RETURN THE MAX SCORE
    else:                   # OTHERWISE IF THERE IS NOT ENOUGH CREDITS LEFT THEN WE CONSIDER THIS A REGULAR EVENT
        return average_interest_score


def _check_age_factor(member_age: int, act: Activity) -> float:
    """
    Does a simple soft score between 0 and 1 based on how age-friendly the activity is.
    The higher the score is for the activity, the more recommended the activity is for the person by age.
    So if an activity has an age range of 0 to 10 years and <member_age> is 5, then the activity is given a score of 1.
    """
    if member_age not in range(act.age_min, act.age_max + 1):
        return 1
    age_window = act.age_max - act.age_min
    if age_window == 0:  # PERFECT MATCH FOR THIS PERSON
        return 1
    # GPT-SUGGESTED CODE BELOW FOR SCORING BASED ON AGE. THE CLOSER A PERSON'S AGE IS TO THE MEDIAN AGE OF THE EVENT
    # THE HIGHER THE EVENT IS SCORED FOR THAT PERSON.
    return 1 - (abs(member_age - (act.age_min + act.age_max) / 2) / (age_window / 2))


if __name__ == "__main__":
    # -----------------------------
    # Define client with extreme-interest scenario
    # -----------------------------
    client_data = {
        "id": "family_extreme_interest_01",
        "party_type": "family",
        "party_members": {
            "Parent 1": {"age": 47, "interest_weights": {"theme_parks": 10, "zoo": 0, "aquarium": 0, "parks": 0}},
            "Parent 2": {"age": 38, "interest_weights": {"theme_parks": 0, "zoo": 0, "aquarium": 0, "parks": 0}},
            "Child 1": {"age": 12, "interest_weights": {"theme_parks": 0, "zoo": 0, "aquarium": 0, "parks": 0}},
            "Child 2": {"age": 8,  "interest_weights": {"theme_parks": 0, "zoo": 0, "aquarium": 0, "parks": 0}}
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
        "day_end_time": "20:00"
    }

    client_data["trip_start"] = datetime.strptime(client_data["trip_start"], "%Y-%m-%d").date()
    client_data["trip_end"] = datetime.strptime(client_data["trip_end"], "%Y-%m-%d").date()

    client = Client(**client_data)

    # -----------------------------
    # Define activity
    # -----------------------------
    event_data = {
        "id": "e_themepark_extreme_01",
        "name": "Thrill Seeker’s Mega Theme Park",
        "category": "theme_parks",
        "tags": ["theme_parks", "roller_coasters", "extreme", "outdoor"],
        "venue": "Wonderland",
        "city": "Toronto",
        "location": {"lat": 43.6426, "lng": -79.3860},
        "duration_min": 180,
        "cost_cad": 80,
        "age_min": 5,
        "age_max": 99,
        "opening_hours": {},
        "fixed_times": [{"date": "2026-08-02", "start": "10:00"}],
        "requires_booking": True,
        "weather_blockers": [],
        "popularity": 0.9
    }

    activity = Activity(**event_data)

    # -----------------------------
    # Compute interest score
    # -----------------------------

    score = interest_score_age(client, activity)
    print(f"Computed interest score for activity '{activity.name}': {score:.2f}")

    # -----------------------------
    # Show which members are extremely interested
    # -----------------------------
    print("\nMember extreme interest status:")
    for member_name, member_info in client.party_members.items():
        interest_score = sum(client.interest(tag, member_name) for tag in activity.tags)
        status = "EXTREMELY INTERESTED" if interest_score >= EXTREME_INTEREST_MIN_SCORE else "Not interested"
        print(f"   {member_name}: {interest_score} → {status}")

    # -----------------------------
    # Show updated credits
    # -----------------------------
    print("\nUpdated credits after scoring:")
    for member, creds in client.credits_left.items():
        print(f"  {member}: {creds}")
