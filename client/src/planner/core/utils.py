# src/planner/core/utils.py
import json
from datetime import date
from pathlib import Path
from typing import List
from .models import Location, Client, Activity

DATA_DIR = Path(__file__).parent.parent / "data"

def place_to_activity(place: dict, city: str,
                      default_duration_min: int = 60,
                      default_cost_cad: float = 0.0) -> Activity:
    """Convert a Google Places result into our Activity model (food)."""
    loc = place["geometry"]["location"]  # {"lat": .., "lng": ..}
    rating = place.get("rating", 0.0)

    # very light cuisine tagging if available (safe fallback to [])
    cuisines = []
    for term in (place.get("types") or []):
        if term in {"restaurant","meal_takeaway","cafe","bakery","bar"}:
            continue
        cuisines.append(term.replace("_", "-"))

    tags = ["food", "restaurant"] + cuisines

    return Activity(
        id=f"rest_{place.get('place_id','unknown')}",
        name=place.get("name", "Restaurant"),
        category="food",
        tags=tags,
        venue=place.get("vicinity", place.get("name","")),
        city=city,
        location=Location(float(loc["lat"]), float(loc["lng"]), city),
        duration_min=default_duration_min,
        cost_cad=default_cost_cad,
        age_min=0, age_max=99,
        opening_hours={"daily": ["10:00","22:00"]},
        fixed_times=[],
        requires_booking=False,
        weather_blockers=[],
        popularity=float(rating) / 5.0,   # map 0..5 -> 0..1
        vibe_tags=[],
    )

def load_people(path: Path = DATA_DIR / "people.json") -> List[Client]:
    raw = json.loads(Path(path).read_text())
    out = []
    for d in raw:
        c = Client(
            id=d["id"],
            party_type=d["party_type"],
            party_members=d.get("party_members", {}),
            religion=d.get("religion"),
            ethnicity_culture=d.get("ethnicity_culture", []),
            vibe=d.get("vibe", ""),
            budget_total=d.get("budget_total", 0.0),
            trip_start=date.fromisoformat(d["trip_start"]),
            trip_end=date.fromisoformat(d["trip_end"]),
            home_base=Location(
                d["home_base"]["lat"],
                d["home_base"]["lng"],
                d["home_base"].get("city", "")
            ),
            avoid_long_transit=d.get("avoid_long_transit", 0),
            prefer_outdoor=d.get("prefer_outdoor", 0),
            prefer_cultural=d.get("prefer_cultural", 0),
            day_start_time=d.get("start_time", "0:00"),
            day_end_time=d.get("end_time", "23:59"),
            early_risers=d.get("early_risers", False),
            # NEW: pass through if your Client supports these
            dietary=d.get("dietary", {"restrictions": [], "avoid": [], "cuisine_likes": []}),
            meal_prefs=d.get("meal_prefs", {
                "breakfast": {"start": "08:00", "end": "10:00"},
                "lunch":     {"start": "12:00", "end": "14:00"},
                "dinner":    {"start": "18:00", "end": "20:00"},
            }),
        )
        out.append(c)
    return out

def load_events(path: Path = DATA_DIR / "events.json") -> List[Activity]:
    raw = json.loads(Path(path).read_text())
    out = []
    for d in raw:
        loc = Location(d["location"]["lat"], d["location"]["lng"], d.get("city", ""))
        a = Activity(
            id=d["id"],
            name=d["name"],
            category=d["category"],
            tags=d.get("tags", []),
            venue=d.get("venue",""),
            city=d.get("city",""),
            location=loc,
            duration_min=d.get("duration_min", 60),
            cost_cad=d.get("cost_cad", 0.0),
            age_min=d.get("age_min", 0),
            age_max=d.get("age_max", 99),
            opening_hours=d.get("opening_hours", {}),
            fixed_times=d.get("fixed_times", []),
            requires_booking=d.get("requires_booking", False),
            weather_blockers=d.get("weather_blockers", []),
            popularity=d.get("popularity", 0.0),
            # NEW: keep vibe tags you added in events.json
            vibe_tags=d.get("vibe_tags", []),
        )
        # Set energy_level if provided in JSON (optional)
        if "energy_level" in d:
            a.energy_level = float(d["energy_level"])
        out.append(a)
    return out


def to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)
