# backend/search_engine.py
from __future__ import annotations
from pathlib import Path
import json, math
from typing import Any, Dict, List, Optional, Tuple, Literal


class HotelSearchEngine:

    def __init__(self):

        base_dir = Path(__file__).resolve().parent  # .../client/src/backend
        data_file = base_dir / "data" / "hotels.mock.json"
        with data_file.open("r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.budget = (None, None)
        self.location = ""
        self.travellers = 0
        self.dates = (None, None)  # index 0: checking, index 1: checkout
        self.min_rating = None
        self.cancellation = {"24h": False, "48h": False, "Free": False, "Any": False}
        self.payment = {"Online": False, "In-person": False, "Any": False}

    def set_budget(self, minimum: float, maximum: float) -> None:
        self.budget = (minimum, maximum)

    def set_location(self, location: str) -> None:
        self.location = location

    def set_travellers(self, ppl: int):
        self.travellers = ppl

    def set_dates(self, date: Tuple[str, str]) -> None:

        self.dates = date

    def set_rating(self, min_rating: int) -> None:
        self.min_rating = min_rating

    def set_cancellation(self, policy_type: str) -> None:
        self.cancellation[policy_type] = True

    def set_payment(self, pmnt_type: str) -> None:

        self.payment[pmnt_type] = True

    def unselect_cancellation(self, policy_type: str) -> None:
        self.cancellation[policy_type] = False

    def unselect_payment(self, pmnt_type: str) -> None:

        self.payment[pmnt_type] = False

    def scrape_json(self, location, budget, travellers, min_rating, can_policy, pmt_policy):

        shortlist = []
        lo, hi = budget

        for hotel in self.data:
            if hotel.get("city") != location:
                continue

            if min_rating is not None and hotel.get("rating", 0) < min_rating:
                continue

            price = hotel["pricePerNight"]
            if lo is not None and price < lo:
                continue

            if hi is not None and price > hi:
                continue

            # cancellation: keep if Any OR matches
            if not (can_policy == "Any" or hotel.get("cancellationPolicy") == can_policy):
                continue

            # payment: keep if Any OR included
            if not (pmt_policy == "Any" or pmt_policy in hotel.get("paymentOptions", [])):
                continue

            if travellers and hotel.get("roomOccupancyMax", 0) < travellers:
                continue

            shortlist.append(hotel)

        return shortlist

    def _bayesian_review_weight(self, rating: float, reviews: int, prior: float = 3.9, m: int = 150) -> float:
        # Higher reviews pull the score toward the true rating; low-review items get pulled toward the prior.
        v = max(0, int(reviews))
        return (v / (v + m)) * float(rating) + (m / (v + m)) * float(prior)

    def _rank_key(self, h):
        # 1) price in ascending order
        price = h.get("pricePerNight", float("inf"))

        # 2) review weight (descending) via negative sign)
        rating = float(h.get("rating", 0.0))
        reviews = int(h.get("reviewsCount", 0))
        review_weight = self._bayesian_review_weight(rating, reviews)

        # 3) amenities (desc) — since no user prefs yet, just total count
        ams = set(a.lower() for a in h.get("amenities", []))
        extra_amenities = len(ams)

        # 4) distance (asc)
        dist = h.get("distanceKmFromAirport")
        dist_val = dist if dist is not None else float("inf")

        # Tuple order enforces priorities; negate where we want descending
        return (price, -review_weight, -extra_amenities, dist_val)

    def search(self):

        cancel_policy = None
        payment_policy = None

        for key in self.cancellation:
            if self.cancellation[key] is True:
                cancel_policy = key

        if cancel_policy is None:
            cancel_policy = "Any"

        for key in self.payment:
            if self.payment[key] is True:
                payment_policy = key

        if payment_policy is None:
            payment_policy = "Any"

        shortlisted = self.scrape_json(self.location, self.budget, self.travellers, self.min_rating,
                                       cancel_policy, payment_policy)

        if len(shortlisted) == 0:
            print("No Suitable Match Found But Here Are Options To Explore")

        # Now shortlisted has the hotels that matches users preference
        # We have to sort these hotel with giving the following priority
        # Price (later we can add a price filter to the UI as well)
        # Review weightage (based on number of reviews and the avg rating) -> we use Baysian for this
        # Higher number of amenties on top what they asked for (If asked)
        # Distance from airport (closest to farthest)

        shortlisted.sort(key=self._rank_key)

        return shortlisted


if __name__ == "__main__":
    eng = HotelSearchEngine()
    eng.set_location("Mississauga")
    eng.set_budget(120, 220)
    eng.set_travellers(2)
    eng.set_rating(3.5)
    eng.set_cancellation("Any")
    eng.set_payment("Any")

    results = eng.search()
    for h in results[:5]:
        print(h["name"], h["pricePerNight"], h["rating"], h.get("reviewsCount"), h.get("distanceKmFromAirport"))
