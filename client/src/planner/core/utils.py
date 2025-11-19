# src/planner/core/utils.py
import json
from datetime import date
from pathlib import Path
from typing import List
from .models import Location, Client, Activity

DATA_DIR = Path(__file__).parent.parent / "data"

def load_people(path: Path = DATA_DIR / "people.json") -> List[Client]:
    raw = json.loads(Path(path).read_text())
    out = []
    for d in raw:
        c = Client(
            id=d["id"],
            party_type=d["party_type"],
            adults_ages=d.get("adults_ages", []),
            kids_ages=d.get("kids_ages", []),
            religion=d.get("religion"),
            ethnicity_culture=d.get("ethnicity_culture", []),
            interest_weights=d.get("interest_weights", {}),
            vibe=d.get("vibe", ""),
            budget_total=d.get("budget_total", 0.0),
            trip_start=date.fromisoformat(d["trip_start"]),
            trip_end=date.fromisoformat(d["trip_end"]),
            home_base=Location(d["home_base"]["lat"], d["home_base"]["lng"], d["home_base"].get("city", "")),
            avoid_long_transit=d.get("avoid_long_transit", 0),
            prefer_outdoor=d.get("prefer_outdoor", 0),
            prefer_cultural=d.get("prefer_cultural", 0),
            early_risers=d.get("early_risers", False),
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
        )
        out.append(a)
    return out

def to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)