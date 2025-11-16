from pathlib import Path
import json
from typing import Any, Dict, List, Optional, Tuple

class FlightTracker:

    def __init__(self):
        self.airport_code = None

    def set_airport(self, airport_code: str) -> None:
        if airport_code and len(airport_code) == 3 and airport_code.isalpha():
            self.airport_code = airport_code
        else:
            self.airport_code = None
    
    def get_flights(self) -> Dict:
        """
        Get all flights for the airport that is selected.
        """
        if not self.airport_code:
            return {
                "error": "Invalid airport code.",
                "flights": []
            }

        mock_flights = self._get_mock_data()

        return {
            "airport": self.airport_code,
            "airportName": self._get_airport_name(self.airport_code),
            "flights": mock_flights
        }
    
    def _get_airport_name(self, code: str) -> str:
        """Get full airport name from code"""
        airport_names = {
            "LAX": "Los Angeles International Airport",
            "JFK": "John F. Kennedy International Airport",
            "ORD": "O'Hare International Airport",
            "YYZ": "Toronto Pearson International Airport",
            "ATL": "Hartsfield-Jackson Atlanta International Airport",
            "DFW": "Dallas/Fort Worth International Airport"
        }
        return airport_names.get(code, f"{code} Airport")

    def _get_mock_data(self) -> List[Dict]:
        """Generate mock flight data for testing"""
        return [
            {
                "flightNumber": "AA123",
                "airline": "American Airlines",
                "destination": "New York (JFK)",
                "scheduledDeparture": "10:30 AM",
                "actualDeparture": "10:35 AM",
                "status": "Departed",
                "gate": "A12",
                "terminal": "1"
            },
            {
                "flightNumber": "DL456",
                "airline": "Delta",
                "destination": "Atlanta (ATL)",
                "scheduledDeparture": "11:00 AM",
                "actualDeparture": "11:30 AM",
                "status": "Delayed",
                "gate": "B5",
                "terminal": "2"
            },
            {
                "flightNumber": "UA789",
                "airline": "United",
                "destination": "Chicago (ORD)",
                "scheduledDeparture": "12:15 PM",
                "actualDeparture": None,
                "status": "On Time",
                "gate": "C3",
                "terminal": "1"
            },
            {
                "flightNumber": "WS101",
                "airline": "WestJet",
                "destination": "Toronto (YYZ)",
                "scheduledDeparture": "1:45 PM",
                "actualDeparture": None,
                "status": "Boarding",
                "gate": "D7",
                "terminal": "3"
            }
        ]