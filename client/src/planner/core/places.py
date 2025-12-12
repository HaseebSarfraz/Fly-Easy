# src/planner/core/places.py
import os, math, requests

GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

def _get(url, params):
    r = requests.get(url, params=params, timeout=10)
    try:
        data = r.json()
    except Exception:
        data = {"status":"BAD_JSON", "results":[]}
    return data

def fetch_nearby_food(lat, lng, radius_m=1200, query=None, opennow=True):
    if not GOOGLE_PLACES_KEY:
        return {"status":"NO_KEY", "results":[]}

    if query:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{query} restaurant",
            "location": f"{lat},{lng}",
            "radius": radius_m,
            "key": GOOGLE_PLACES_KEY,
        }
        # TextSearch ignores opennow in some cases; acceptable.
    else:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius_m,
            "type": "restaurant",
            "key": GOOGLE_PLACES_KEY,
        }
        if opennow:
            params["opennow"] = "true"

    return _get(url, params)
