from pathlib import Path
import json
import requests
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

class FlightTracker:

    def __init__(self, airport_data_file: str = "./data/airport_tracker_codes.json"):
        self.airport_code = None
        self.api_key = "a75d212df3msh80b4775bd20989bp1ac458jsn28c53dce7038"
        self.api_host = "aerodatabox.p.rapidapi.com"
        
        self.static_airports = self._load_airport_data(airport_data_file)
        
        self.flight_cache = {}
        self.airport_info_cache = {}
        
        self.FLIGHT_CACHE_DURATION = 300  # 5 minutes
        self.AIRPORT_CACHE_DURATION = 86400  # 24 hours
        
        self.api_calls = {
            'flights': 0,
            'airport_info': 0,
            'total': 0
        }

    def _load_airport_data(self, filepath: str) -> dict:
        """Load static airport data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Airport data file not found: {filepath}")
            return {}
        except json.JSONDecodeError:
            print(f"Invalid JSON in airport data file: {filepath}")
            return {}

    def set_airport(self, airport_code: str) -> None:
        if airport_code and len(airport_code) == 3 and airport_code.isalpha():
            self.airport_code = airport_code
        else:
            self.airport_code = None
    
    def get_flights(self, direction: str = "Both") -> Dict:
        """
        Get all flights for the airport that is selected.
        """
        if not self.airport_code:
            return {
                "error": "Invalid airport code.",
                "flights": []
            }
        try:
            flights = self._fetch_flights(direction)
            return {
                "airport": self.airport_code,
                "airportName": self._get_airport_info(self.airport_code),
                "flights": flights,
                "direction": direction,
                "cached": self._is_cache_valid(f"{self.airport_code}_{direction}", self.flight_cache, self.FLIGHT_CACHE_DURATION)
            }
        except Exception as e:
            print(f"Error fetching flights: {e}")
            return {
                "error": f"Failed to fetch flight data: {str(e)}",
                "flights": []
            }
    
    def _is_cache_valid(self, cache_key: str, cache_dict: dict, duration: int) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in cache_dict:
            return False
        
        cached_time = cache_dict[cache_key].get('timestamp', 0)
        return (time.time() - cached_time) < duration
    
    def _fetch_flights(self, direction: str) -> List[Dict]:
        cache_key = f"{self.airport_code}_{direction}"
        
        if self._is_cache_valid(cache_key, self.flight_cache, self.FLIGHT_CACHE_DURATION):
            print(f"✓ Using cached flight data for {cache_key}")
            return self.flight_cache[cache_key]['data']
        
        print(f"→ Fetching fresh flight data from API for {cache_key}")
        self.api_calls['flights'] += 1
        self.api_calls['total'] += 1
        
        url = f"https://{self.api_host}/flights/airports/iata/{self.airport_code}"

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }

        params = {
            "offsetMinutes": -30,
            "durationMinutes": 720,
            "withLeg": "true",
            "direction": "Both",
            "withCancelled": "false",
            "withCodeshared": "true",
            "withCargo": "false",
            "withPrivate": "false",
            "withLocation": "false"
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        flights = []

        if direction == "Departure" or direction == "Both":
            departures = data.get("departures", [])
            for flight in departures:
                flights.append(self._parse_flight(flight, "Departure"))
        
        if direction == "Arrival" or direction == "Both":
            arrivals = data.get("arrivals", [])
            for flight in arrivals:
                flights.append(self._parse_flight(flight, "Arrival"))
        
        result = flights
        
        self.flight_cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
        
        print(f"  Cached {len(result)} flights. Total API calls: {self.api_calls['total']}")
        
        return result
    
    def _parse_flight(self, flight: Dict, flight_type: str) -> Dict:
        airline = flight.get("airline", {})
        
        departure_info = flight.get("departure", {})
        arrival_info = flight.get("arrival", {})
        
        departure_airport = departure_info.get("airport", {})
        arrival_airport = arrival_info.get("airport", {})
        
        if flight_type == "Departure":
            time_info = departure_info
            other_airport = arrival_airport.get("name", "Unknown")
        else:  
            time_info = arrival_info
            other_airport = departure_airport.get("name", "Unknown")
        
        scheduled = time_info.get("scheduledTime", {}).get("local", "")
        actual = time_info.get("actualTime", {}).get("local") or time_info.get("revisedTime", {}).get("local")
        
        airport_resources = time_info.get("airportResources", {}) or {}
        gate = time_info.get("gate") or airport_resources.get("gate")
        terminal = time_info.get("terminal") or airport_resources.get("terminal")
        if not gate:
            gate = departure_info.get("gate") or arrival_info.get("gate")
        if not terminal:
            terminal = departure_info.get("terminal") or arrival_info.get("terminal")
        gate = gate or "TBA"
        terminal = terminal or "TBA"
        
        return {
            "flightNumber": flight.get("number", "N/A"),
            "airline": airline.get("name", "Unknown"),
            "departure": departure_airport.get("name", "Unknown"),
            "arrival": arrival_airport.get("name", "Unknown"),
            "country": arrival_airport.get("iata", "") if flight_type == "Departure" else departure_airport.get("iata", ""),
            "city": other_airport,
            "scheduledTime": self._format_time(scheduled),
            "actualTime": self._format_time(actual),
            "status": flight.get("status", "Scheduled"),
            "gate": gate,
            "terminal": terminal,
            "type": flight_type,
            "aircraft": flight.get("aircraft", {}).get("model", "Unknown")
        }
    
    def _format_time(self, time_str):
        if not time_str:
            return None
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime("%I:%M %p")
        except:
            return time_str
    
    def _get_airport_info(self, code: str) -> str:
        """Fetch airport name - first from static data, then cache, then API"""
        
        # 1. Check static data first (no API call needed!)
        if code in self.static_airports:
            print(f"✓ Using static airport data for {code}")
            return self.static_airports[code]
        
        # 2. Check cache
        if self._is_cache_valid(code, self.airport_info_cache, self.AIRPORT_CACHE_DURATION):
            print(f"✓ Using cached airport info for {code}")
            return self.airport_info_cache[code]['data']
        
        # 3. Last resort: fetch from API
        print(f"→ Fetching airport info from API for {code}")
        self.api_calls['airport_info'] += 1
        self.api_calls['total'] += 1
        
        try:
            url = f"https://{self.api_host}/airports/iata/{code}"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            airport_name = data.get("fullName", f"{code} Airport")
            
            # Cache the result
            self.airport_info_cache[code] = {
                'data': airport_name,
                'timestamp': time.time()
            }
            
            print(f"  Total API calls: {self.api_calls['total']}")
            
            return airport_name
        except:
            return f"{code} Airport"
    
    def clear_cache(self):
        """Clear all cached data"""
        self.flight_cache.clear()
        self.airport_info_cache.clear()
        print("Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about cached data"""
        return {
            "flight_cache_entries": len(self.flight_cache),
            "airport_cache_entries": len(self.airport_info_cache),
            "flight_cache_keys": list(self.flight_cache.keys()),
            "airport_cache_keys": list(self.airport_info_cache.keys()),
            "api_calls": self.api_calls,
            "static_airports_loaded": len(self.static_airports)
        }
    
    def reset_api_counter(self):
        """Reset API call counter"""
        self.api_calls = {
            'flights': 0,
            'airport_info': 0,
            'total': 0
        }