from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union

class Location: 

    lat: float
    lng: float 
    city: str

    def __init__(self, lat: float, lng: float, city: str):

        self.lat = lat
        self.lng = lng
        self.city = city


    def get_location(self):
        return (self.lat, self.lng, self.city )
    

class Client: 
    id: str
    party_type: str                 # "family", "couple", "solo", ...
    party_members: Dict[str, Union[str, Dict]]       # Each family member's age and their weighted interests.
    religion: Optional[str]
    ethnicity_culture: List[str]
    vibe: str
    budget_total: float
    trip_start: date
    trip_end: date
    home_base: Location
    avoid_long_transit: int         # 0–10 in your data
    prefer_outdoor: int             # 0–10
    prefer_cultural: int            # 0–10
    day_start_time: time
    day_end_time: time
    day_start_min: int              # STARTING TIME FOR THEIR DAY (IN MINUTES)
    day_end_min: int                # ENDING TIME FOR THEIR DAY (IN MINUTES)
    credits_left: Dict[str, int]    # KEEPS A COUNT OF THE NUMBER OF ACCOMMODATION CREDITS LEFT FOR EVERY MEMBER


    def __init__(
        self,
        id: str,
        party_type: str,                 # "family", "couple", "solo", ...
        party_members: Dict[str, Union[str, Dict]],
        religion: Optional[str],
        ethnicity_culture: List[str],
        vibe: str,
        budget_total: float,
        trip_start: date,
        trip_end: date,
        home_base: Location,
        avoid_long_transit: int,         # 0–10
        prefer_outdoor: int,             # 0–10
        prefer_cultural: int,            # 0–10
        day_start_time: str,
        day_end_time: str
    ):
        
        self.party_members = party_members
        self.id = str(id)
        self.party_type = party_type
        self.religion = religion
        self.ethnicity_culture = ethnicity_culture
        self.vibe = vibe
        self.budget_total = float(budget_total)
        self.trip_start = trip_start
        self.trip_end = trip_end
        self.home_base = home_base
        self.avoid_long_transit = int(avoid_long_transit)
        self.prefer_outdoor = int(prefer_outdoor)
        self.prefer_cultural = int(prefer_cultural)
        self.day_start_time = datetime.strptime(day_start_time, "%H:%M").time()
        self.day_end_time = datetime.strptime(day_end_time, "%H:%M").time()
        self.day_start_min, self.day_end_min = _window_to_minutes(_to_minutes(day_start_time), _to_minutes(day_end_time))
        self.credits_left = {}
        # CODE BELOW GETS THE NUMBER OF CREDITS PER MEMBER
        trip_days = (trip_end - trip_start).days
        cpm = math.floor(trip_days // len(self.party_members))
        for name in self.party_members:
            self.credits_left[name] = cpm

        # THE NUMBER OF HOURS EACH MEMBER CAN GET PER EVENT IN THE DAY (ASSUMING RIGHT NOW THAT IT IS EQUAL PER PERSON)
        self.total_day_duration = self.day_end_min - self.day_start_min
        self.daily_act_time_per_member = self.total_day_duration / len(self.party_members)
        self.engagement_time = {}
        for name in self.party_members:
            self.engagement_time[name] = 0

        # STORES THE NUMBER OF TIMES EACH MEMBER WAS SATISFIED.
        self.times_satisfied = {}
        for name in party_members:
            self.times_satisfied[name] = 0

    def size(self) -> int:
        return len(self.party_members)

    def min_age(self) -> int:
        ages = [self.party_members[m]["age"] for m in self.party_members]
        if ages:
            return min(ages)
        return 0

    def interest(self, activity: str, name: str):
        """
        Returns the activity interest score for <name>.
        """
        if activity in self.party_members[name]["interest_weights"]:
            return self.party_members[name]["interest_weights"][activity]
        else:
            return 0


class Activity:
    def __init__(
        self,
        id: str,
        name: str,
        category: str,
        tags: list[str],
        venue: str,
        city: str,
        location: Location,          # The Location class we created above
        duration_min: int,
        cost_cad: float,
        age_min: int,
        age_max: int,
        opening_hours: dict,         # {} or {"daily":["09:00","21:00"]} or {"Wed":["10:00","21:00"], ...}
        fixed_times: list[dict],     # [{"date":"YYYY-MM-DD","start":"HH:MM"}, ...]
        requires_booking: bool,
        weather_blockers: list[str],
        popularity: float,
    ):
        self.id = str(id)
        self.name = name
        self.category = category
        self.tags = list(tags)
        self.venue = venue
        self.city = city
        self.location = location
        self.duration_min = int(duration_min)
        self.cost_cad = float(cost_cad)
        self.age_min = int(age_min)
        self.age_max = int(age_max)
        self.opening_hours = dict(opening_hours or {})
        self.fixed_times = list(fixed_times or [])
        self.requires_booking = bool(requires_booking)
        self.weather_blockers = list(weather_blockers or [])
        self.popularity = float(popularity)


  # helpers we might need.
    def __str__(self):
        return (
            f"Activity({self.name} | ID: {self.id})\n"
            f"  Category: {self.category}\n"
            f"  Venue: {self.venue}, {self.city}\n"
            f"  Duration: {self.duration_min} min | Cost: ${self.cost_cad:.2f}\n"
            f"  Age range: {self.age_min}-{self.age_max}\n"
            f"  Popularity: {self.popularity:.2f}\n"
            f"  Opening hours: {self.opening_hours}\n"
            f"  Fixed times: {self.fixed_times}\n"
            f"  Requires booking: {self.requires_booking}\n"
            f"  Weather blockers: {self.weather_blockers}\n"
            f"  Tags: {self.tags}\n"
            f"  Location: ({self.location.lat}, {self.location.lng})"
        )

    def _weekday_key(self, d: date) -> str:
        # "Mon","Tue","Wed","Thu","Fri","Sat","Sun"
        return ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][d.weekday()]

    def _window_for_date(self, d: date) -> tuple[int, int] | None:

        if "daily" in self.opening_hours:
            s, e = self.opening_hours["daily"]
            return _to_minutes(s), _to_minutes(e)

        wk = self._weekday_key(d)
        if wk in self.opening_hours:
            s, e = self.opening_hours[wk]
            return _to_minutes(s), _to_minutes(e)

        return None

    def can_start_at(self, start_dt: datetime) -> bool:
        """
        If there are fixed times, the activity must start exactly at one of them (same date+time).
        Otherwise, it must fit within the daily/weekday window for that date.
        """
        # fixed showtimes / games / concerts
        if self.fixed_times:
            for ft in self.fixed_times:
                if ft.get("date") == start_dt.date().isoformat() and ft.get("start") == start_dt.strftime("%H:%M"):
                    return True
            return False

        # regular opening hours
        window = self._window_for_date(start_dt.date())
        if window is None:
            return False
        s_min, e_min = window
        start_min = start_dt.hour * 60 + start_dt.minute
        return (start_min >= s_min) and (start_min + self.duration_min) <= e_min

class PlanEvent:
    activity: Activity
    start_dt: datetime
    end_dt: datetime
    def __init__(self, activity: Activity, start_dt: datetime):
        self.activity = activity
        self.start_dt = start_dt
        self.end_dt = start_dt + timedelta(minutes=activity.duration_min)

    def __repr__(self) -> str:
        a = self.activity
        return f"PlanEvent({self.start_dt.time()}–{self.end_dt.time()} {a.name})"


class PlanDay:
    events: list[PlanEvent]
    def __init__(self, day: date):
        self.day = day
        self.events = []
        self.tags_encountered = {}

    def add(self, event: PlanEvent):
        self.events.append(event)

    # helpers we might need
    def total_cost(self) -> float:
        return sum(event.activity.cost_cad for event in self.events)

    def last_event_end(self) -> Optional[datetime]:
        return self.events[-1].end_dt if self.events else None

def _to_minutes(hhmm: str) -> int:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)


def _window_to_minutes(w_start: int, w_end: int) -> tuple[int, int]:
    if w_end < w_start:
        w_end += (24 * 60)
    return w_start, w_end
if __name__ == "__main__":
    from datetime import date, datetime

    # ---- tiny hard checks we’ll reuse ----
    def hc_age_ok(client, act) -> bool:
        return client.min_age() >= act.age_min and client.min_age() <= act.age_max

    def hc_open_window_ok(act, start_dt: datetime) -> bool:
        return act.can_start_at(start_dt)

    # ---- mock data ----
    home = Location(43.65, -79.38, "Toronto")

    client = Client(
        id="p1",
        party_type="family",
        adults_ages=[30, 29],
        kids_ages=[9],                        # min age = 9
        religion=None,
        ethnicity_culture=[],
        interest_weights={"concerts": 8, "museum": 5},
        vibe="chill",
        budget_total=1200.0,
        trip_start=date(2025, 8, 3),
        trip_end=date(2025, 8, 6),
        home_base=home,
        avoid_long_transit=5,
        prefer_outdoor=6,
        prefer_cultural=7,
        early_risers=True,
    )

    # Fixed-time concert (from your JSON style)
    concert = Activity(
        id="e_concert_southasian_01",
        name="Arijit Singh Live",
        category="concert",
        tags=["concerts", "bollywood", "south_asian"],
        venue="Scotiabank Arena",
        city="Toronto",
        location=home,
        duration_min=150,
        cost_cad=120,
        age_min=8,
        age_max=99,
        opening_hours={},
        fixed_times=[{"date": "2025-08-03", "start": "17:00"}],
        requires_booking=True,
        weather_blockers=[],
        popularity=0.95,
    )

    # Opening-hours museum (daily 10:00–17:30, 150 mins)
    rom = Activity(
        id="e_rom_01",
        name="Royal Ontario Museum",
        category="museum",
        tags=["history", "science", "indoors", "culture"],
        venue="ROM",
        city="Toronto",
        location=home,
        duration_min=150,
        cost_cad=26,
        age_min=0,
        age_max=99,
        opening_hours={"daily": ["10:00", "17:30"]},
        fixed_times=[],
        requires_booking=False,
        weather_blockers=[],
        popularity=0.87,
    )

    # ---- sanity checks ----
    # 1) Concert exact time
    start_ok   = datetime(2025, 8, 3, 17, 0)
    start_bad1 = datetime(2025, 8, 3, 18, 0)
    start_bad2 = datetime(2025, 8, 4, 17, 0)

    print("Concert — age ok:", hc_age_ok(client, concert))                 # expect True (9 ≥ 8)
    print("Concert — exact 17:00 fits:", hc_open_window_ok(concert, start_ok))       # True
    print("Concert — 18:00 fits:", hc_open_window_ok(concert, start_bad1))           # False
    print("Concert — next day 17:00 fits:", hc_open_window_ok(concert, start_bad2))  # False

    # 2) ROM windows
    rom_15 = datetime(2025, 8, 4, 15, 0)   # 15:00 + 150 = 17:30 -> fits
    rom_1601 = datetime(2025, 8, 4, 16, 1) # 16:01 + 150 = 18:31 -> past close

    print("ROM — age ok:", hc_age_ok(client, rom))                         # True
    print("ROM — 15:00 fits:", hc_open_window_ok(rom, rom_15))             # True
    print("ROM — 16:01 fits:", hc_open_window_ok(rom, rom_1601))           # False

    # Optional asserts to fail fast during development
    assert hc_age_ok(client, concert)
    assert hc_open_window_ok(concert, start_ok)
    assert not hc_open_window_ok(concert, start_bad1)
    assert not hc_open_window_ok(concert, start_bad2)
    assert hc_open_window_ok(rom, rom_15)
    assert not hc_open_window_ok(rom, rom_1601)

    print("\nAll sanity checks passed ✅")
