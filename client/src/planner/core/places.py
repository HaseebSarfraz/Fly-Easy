# src/planner/core/places.py
import os, math, requests
from dotenv import load_dotenv

load_dotenv()

def _get_google_places_key():
    """Get the API key, reading from environment each time."""
    key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not key:
        print("[places] WARNING: GOOGLE_PLACES_API_KEY not found in environment!")
    else:
        print(f"[places] API key loaded: {key[:10]}...{key[-4:]}")  # Debug print
    return key

def _get(url, params):
    """Make API request and return response data with proper error handling."""
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
        
        try:
            data = r.json()
        except ValueError as e:
            print(f"[places] Failed to parse JSON response: {e}")
            return {"status": "BAD_JSON", "results": [], "error_message": str(e)}
        
        # Google Places API returns status in the JSON response
        api_status = data.get("status", "UNKNOWN")
        
        # Log non-OK statuses for debugging
        if api_status != "OK" and api_status != "ZERO_RESULTS":
            error_msg = data.get("error_message", "No error message provided")
            print(f"[places] API returned status '{api_status}': {error_msg}")
        
        # Ensure results list exists
        if "results" not in data:
            data["results"] = []
            
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"[places] HTTP request failed: {e}")
        return {"status": "HTTP_ERROR", "results": [], "error_message": str(e)}
    except Exception as e:
        print(f"[places] Unexpected error: {e}")
        return {"status": "UNKNOWN_ERROR", "results": [], "error_message": str(e)}

def fetch_nearby_food(lat, lng, radius_m=1200, query=None, opennow=True):
    api_key = _get_google_places_key()
    if not api_key:
        print("[places] ERROR: GOOGLE_PLACES_API_KEY environment variable is not set!")
        return {"status": "NO_KEY", "results": []}

    if query:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{query} restaurant",
            "location": f"{lat},{lng}",
            "radius": radius_m,
            "key": api_key,  # Use the dynamically read key
        }
    else:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius_m,
            "type": "restaurant",
            "key": api_key,
        }
        if opennow:
            params["opennow"] = "true"

    return _get(url, params)

if __name__ == "__main__":
    key = _get_google_places_key()
    print(f"Key loaded: {'YES' if key else 'NO'}")
    if key:
        # Test API call
        result = fetch_nearby_food(43.653, -79.383, query="pizza")
        print(f"Status: {result.get('status')}")
        print(f"Results: {len(result.get('results', []))}")