# Planner Design and Constraint Handling

This document explains the internal design decisions, data structures, and constraint-handling logic used by our planner. The goal is to clearly describe *what* the planner enforces, *why* those choices were made, and *how* they are implemented algorithmically.

---

## 1. Hard vs Soft Constraints

### Hard Constraints

Hard constraints define **feasibility**. Any plan violating these is considered invalid and must be repaired or rejected.

The planner enforces the following hard constraints:

* **Time Window Constraints**: All events must occur within the client’s daily start and end times.
* **Fixed-Time Events**: Events with immutable times (e.g., concerts) cannot be moved or overlapped.
* **Physical Overlap Constraints**: No two events may overlap in time.
* **Age / Eligibility Constraints**: Activities must be appropriate for all travelers.
* **Opening Hours Constraints**: Activities must occur while locations are open.
* **Weather Feasibility Constraints**: Outdoor activities are checked against the forecast to ensure they can be safely and reasonably attended.

Violating any hard constraint triggers event replacement, removal, or rescheduling.

### Soft Constraints

Soft constraints encode **preferences and quality signals** rather than feasibility.

Listed below are all the soft constraints taken into consideration:

* Staying within a daily budget target
* Matching preferred cuisines or activity categories
* Minimizing schedule disruption (nudging / Repairs)
* Balancing activity diversity and duration across the day

Soft constraint violations do not invalidate a plan. Instead, they reduce the **score** of affected activities, influencing ranking and selection. The scoring and penalization mechanism is described in detail in Section 11.

---

## 2. Activity Places to Consider

Candidate activities are drawn from:

* Fixed activity datasets
* Google Places search results (restaurants only)

Each candidate is pre-filtered by:

* Category relevance
* Cost availability
* Location metadata
* Suitability for the group

This ensures the planner searches over *reasonable* options rather than an unbounded activity space.

---

## 3. JSON Structure Design

Input JSON files are structured to cleanly separate concerns while remaining expressive enough to support personalization and constraint enforcement. Below we describe the two core schemas used by the planner.

### 3.1 People JSON (Traveler & Trip Specification)

The **People JSON** defines *who* is traveling, *how* they prefer to travel, and *what constraints* must be respected. On a high level, each JSON object contains the following information:

* **Party composition**: Each traveler is defined with an age and weighted interests.
* **Interest weights**: Numeric weights allow the planner to score candidate activities by aggregating preferences across the group.
* **Group-level constraints**: Budget, trip dates, daily time windows, and transit tolerance.
* **Dietary constraints & meal preferences**: Per-meal cuisine preferences, time windows, and budget caps.

Key design properties:

* Interest weights are merged conservatively so children’s and adults’ needs are both respected.
* Age fields directly gate activities via hard constraints.
* Meal preferences double as *temporal anchors* for the day.

This structure allows the planner to reason about feasibility (time, age, diet) and quality (interests, vibe) simultaneously.

### 3.2 Events JSON

The **Events JSON** describes fixed or candidate activities that may appear in a plan. A representative example includes:

* **Category and tags**: Used for preference matching and scoring.
* **Location and duration**: Used for time feasibility and ordering.
* **Cost and age limits**: Enforced as budget and eligibility constraints.
* **Fixed times**: Explicit anchors that cannot be moved once placed.
* **Weather blockers and booking requirements**: Additional feasibility signals.

Events with `fixed_times` are treated as immovable anchors, while others remain flexible and may be added, shifted, or removed during planning.

This separation between People JSON and Events JSON allows the same activity catalog to be reused across many traveler profiles.

---

## 4. Personalized Preferences per Traveler

The planner supports per-traveler:

* Activity interest weighting
* Dietary restrictions
* Cuisine preferences

Preferences are merged conservatively across the group, ensuring that:

* No traveler’s hard restriction is violated
* Soft preferences are satisfied where possible

This design avoids dominance by any single traveler.

---

## 5. Trip Expectations

Each trip encodes high-level expectations, such as:

* Relaxed vs packed schedules
* Cultural vs entertainment focus
* Budget sensitivity

These expectations influence:

* Number of activities per day
* Willingness to replace events
* Penalty weighting

---

## 6. Google Places API Usage for Restaurants

The Google Places API is used exclusively for **restaurant discovery**, serving as the planner’s primary mechanism for sourcing meal locations dynamically. Queries are constructed using:

* Cuisine keywords derived from meal preferences
* Price range constraints specified per meal
* Proximity to the current or planned location

Returned results are filtered to ensure feasibility and relevance:

* Dietary compatibility with all travelers
* Compliance with per-meal budget caps
* Deduplication against previously selected restaurants

Approved restaurants are converted into meal events and immediately treated as **temporal anchors**, forming the structural backbone of each day’s schedule.

## 7. Anchor Placement: Meals First

feasible regions for non-food activities

This strategy mirrors human planning behavior and significantly reduces downstream conflicts, resulting in more stable and realistic itineraries.

---

Food events are placed **first** and treated as anchors:

* Breakfast, lunch, and dinner establish temporal structure
* Meal windows are respected strictly
* Meals constrain available time slots for other activities

This mirrors real human planning behavior and stabilizes the schedule.

---

## 8. Fixed Events Placement

Fixed-time events (e.g., concerts, tours) are placed immediately after food anchors.

These events:

* Cannot be moved
* Block surrounding time
* Force nearby activities to adapt

This ordering prevents impossible schedules.

---

## 9. Base Plan Generation and Iterative Refinement

The planner generates itineraries in multiple phases.

### 9.1 Base Plan Generation (Beam Search)

A **beam-search strategy** is used to generate an initial base plan. At each step:

* Candidate activities are scored using a utility function based on group interest satisfaction and vibe alignment.
* Only the top-K partial plans (the beam) are retained.
* Infeasible branches are pruned early using hard constraint checks.

This balances exploration and tractability, enabling the planner to explore diverse high-quality schedules without incurring prohibitive computational cost.

### 9.2 Activity Scoring

Each activity is scored using:

* **Interest score**: Aggregated from per-member interest weights.
* **Extreme interest credits**: Highly interested members may consume limited credits to justify niche activities.
* **Vibe bonus**: Small additive boost when activity vibe aligns with trip vibe.

Activities that satisfy the entire group are naturally favored, but extreme-interest cases are supported in a controlled way.

### 9.3 Incremental Addition and Repair

After laying down the base plan:

* Remaining activities are added greedily if they fit without violating hard constraints.
* If conflicts arise, RepairB may remove or replace lower-scoring activities.
* Activities that cannot be feasibly placed are skipped.

This guarantees feasibility while maximizing overall satisfaction.

---

## 10. Event Sorting Logic

Events within a day are sorted by:

1. Fixed start times
2. Anchor priority (meals)
3. Flexible activities by earliest feasible slot

This guarantees chronological correctness and prevents overlaps.

---

## 11. Penalization and Scoring Model

Scoring serves as the primary mechanism by which soft constraints influence planner behavior. Rather than invalidating plans, violations reduce the relative utility of activities, guiding selection and replacement decisions during optimization.

The planner uses a multi-stage scoring and penalization system to guide optimization.

### 11.1 Interest and Extreme Accommodation

Each activity receives a base interest score computed by aggregating per-member interest weights. When one or more members exhibit **extreme interest**:

* A limited credit system allows up to two extreme accommodations per member.
* Credits correspond to time blocks, preventing over-accommodation.
* If sufficient credits exist, the activity may be scored at the maximum individual interest level.

This prevents dominance by a single traveler while still allowing occasional personalization.

### 11.2 Duration Penalty (Exponential)

Long activities are penalized relative to the total available day duration. The penalty grows exponentially when:

* Average interest is low
* Activity duration consumes a large fraction of the day

This discourages low-value activities from crowding the schedule.

### 11.3 Conflict Penalty (Exponential)

Activities are penalized when they repeat tags already seen earlier in the plan:

* Repetition incurs increasing penalties
* Penalty strength is modulated by average group interest
* Longer activities amplify conflict cost

This promotes diversity while respecting strong preferences.

### 11.4 Final Utility Score

The final score of an activity combines:

* Interest score
* Vibe bonus
* Duration penalty
* Conflict penalty

Soft constraint violations directly reduce this score, influencing which activities are retained or removed.

---

## 12. Weather API Integration

The planner integrates the **OpenMeteo API** to obtain daily weather forecasts for the trip location. Forecast data is used deterministically as part of feasibility checking:

* Activities are labeled as indoor or outdoor
* Outdoor activities are evaluated against forecasted conditions
* Activities deemed infeasible under expected weather are filtered or replaced

Weather feasibility is treated as a **hard constraint**, ensuring that generated itineraries remain realistic and executable under expected conditions.

---

## 13. Google Places for Restaurants

Restaurants are sourced via Google Places using:

* Cuisine keywords
* Price range filters
* Proximity constraints

Results are ranked and sampled to avoid repetition and preserve diversity.

---

## 14. Future updates

During the development phase of the project we came up with more ideas
on what to implement in the future to further extend on this planner's abilities.

### 14.1 Real-time energy-based plan changes

A natural extension is an energy-aware planner. If travelers optionally connect fitness or health trackers (e.g., step count, heart rate variability, sleep quality), the planner could infer real-time fatigue levels to suggest a different plan more suitable to their current energy state. 

This could be done in a number of ways, most notably:
* Reducing events with considerable energy requirements.
* Reducing event density, adding longer and/or more frequent breaks in-between activities.
* Reordering of events to suggest higher-energy events later.

This would allow for a more dynamic activity planner, bringing the planning algorithm's abilities a step closer to a human's mind.

### 14.2 Medical, Physical, and Neurological conditions

Future versions of this planner may consider asking the users for any medical, physical, or neurological conditions so 
that the planner does not suggest activities that can harm them or anyone in their group. Restrictions include:

* Mobility restrictions
* Neurological sensitivities (eg. epilepsy)
* Chronic conditions (eg. cancer, diabetes)

any provided conditions would be treated as hard constraints as a planner must prioritize user safety, making the algorithm
more ethical.

### 14.3 Trip groupings

This is a feature we really wanted to highlight as part of our future plans. **Trip groupings** involve two or more users
in the same city/area during overlapping time window to group together and explore activities together.

This enables:
* Suggesting events popular to socially adjacent families
* Promoting shared events when two or more groups share common interests
* Encouraging social interaction during travel or while attending the event(s)

For example, if one family attends a music-focused event that another similar family has not yet planned, the system may recommend it as a socially reinforced suggestion. 
This improves discovery, shared experiences, and social connectivity without forcing participation.

Together, these future directions highlight the planner’s potential to evolve from a static itinerary generator into a responsive, socially-aware travel companion.

---
## 15. Future planner optimizations

Towards the end of the project, we wanted to consider more external factors which could influence the results of our planner, these include:

### 15.1 Interest score adjusted by the activity's "age curve"

While the planner is able to filter out activities based on age eligibility, it uses a monotone interest scoring system
for every person. This means the planner does not take into account which person would *actually* enjoy the activity more than
the other, even if their interest weights were identical, and it mainly comes down to age. 

Suppose person A is 34 years old, person B is 13 years old, 
and both love amusement parks equally. If Canada's Wonderland is a candidate activity, people of around age 18 enjoy Canada's Wonderland the most,
so in that sense, person B should be given a higher interest score than person A. This means each activity should also have a 
*median* age, representing the age of at least half of its attendees.

### 15.2 Base plan: prioritizing leftover unsatisfied people

When constructing a base plan, there are several factors that can influence the results of the base plan. If weather persists, 
or all of the activities for a certain person cannot be added to the base plan, then this person should be prioritized on the next
day for the base plan's construction so one of their activities gets added first to ensure no overlaps with non-anchor activites.

By incorporating factors such as age-adjusted interest scores and prioritization of unsatisfied attendees, the planner can generate schedules that feel more personalized and human-like, while improving fairness and overall satisfaction across all participants.

---

## Summary

The planner is fundamentally **constraint-first**. Hard constraints guarantee feasibility, while soft constraints guide optimization. The system is intentionally conservative, prioritizing realistic and valid itineraries over perfect preference satisfaction.
