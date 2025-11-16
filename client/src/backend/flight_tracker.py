from pathlib import Path
import json
import requests
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class FlightTracker:

    def __init__(self):
        self.airport_code = None
        self.api_key = "a75d212df3msh80b4775bd20989bp1ac458jsn28c53dce7038"
        self.api_host = "aerodatabox.p.rapidapi.com"

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
                "direction": direction
            }
        except Exception as e:
            print(f"Error fetching flights: {e}")
            return {
                "error": f"Failed to fetch flight data: {str(e)}",
                "flights": []
            }
    
    def _fetch_flights(self, direction: str) -> List[Dict]:
        curr_time = datetime.now()
        from_time = curr_time.strftime("%Y-%m-%dT%H:%M")
        to_time = (curr_time + timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M")

        url = f"https://{self.api_host}/flights/airports/iata/{self.airport_code}"

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }

        params = {
            "offsetMinutes": -120,
            "durationMinutes": 720,
            "withLeg": "true",
            "direction": "Both",
            "withCancelled": "true",
            "withCodeshared": "true",
            "withCargo": "false",
            "withPrivate": "false",
            "withLocation": "false"
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        print(json.dumps(data.get("departures", [])[0], indent=2))
        flights = []

        if direction == "Departure" or direction == "Both":
            departures = data.get("departures", [])
            for flight in departures:
                flights.append(self._parse_flight(flight, "Departure"))
        
        if direction == "Arrival" or direction == "Both":
            arrivals = data.get("arrivals", [])
            for flight in arrivals:
                flights.append(self._parse_flight(flight, "Arrival"))
        
        return flights[:50]
    
    def _parse_flight(self, flight: Dict, flight_type: str) -> Dict:
        airline = flight.get("airline", {})
        
        if flight_type == "Departure":
            location_info = flight.get("arrival", {}).get("airport", {})
            time_info = flight.get("departure", {})
        else:
            location_info = flight.get("departure", {}).get("airport", {})
            time_info = flight.get("arrival", {})
        
        scheduled = time_info.get("scheduledTime", {}).get("local", "")
        actual = time_info.get("actualTime", {}).get("local") or time_info.get("revisedTime", {}).get("local")
        
        return {
            "flightNumber": flight.get("number", "N/A"),
            "airline": airline.get("name", "Unknown"),
            "location": location_info.get("name", "Unknown"),
            "country": location_info.get("iata", ""),
            "city": location_info.get("name", ""),
            "scheduledTime": self._format_time(scheduled),
            "actualTime": self._format_time(actual),
            "status": flight.get("status", "Scheduled"),
            "gate": time_info.get("gate", "TBA"),
            "terminal": time_info.get("terminal", "TBA"),
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
        """Fetch real airport name from API"""
        try:
            url = f"https://{self.api_host}/airports/iata/{code}"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("fullName", f"{code} Airport")
        except:
            return f"{code} Airport"

