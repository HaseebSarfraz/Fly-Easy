# client/src/backend/tests/hotel_tests/test_engine.py
import pytest
import sys, pathlib

# Ensure current backend dir is importable (robust even if run from project root)
BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]  # .../client/src/backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import hotel_search_engine as hse


@pytest.fixture
def sample_hotels():
    return [
        {
            "id": "A",
            "name": "Airport Inn",
            "city": "Mississauga",
            "stars": 3,
            "rating": 4.2,
            "reviewsCount": 1200,
            "distanceKmFromAirport": 3.2,
            "pricePerNight": 140,
            "amenities": ["wifi", "breakfast", "gym"],
            "cancellationPolicy": "Free",
            "paymentOptions": ["Online", "In-person"],
            "roomOccupancyMax": 2,
            "imageUrl": None,
        },
        {
            "id": "B",
            "name": "Transit Lodge",
            "city": "Mississauga",
            "stars": 4,
            "rating": 3.8,
            "reviewsCount": 180,
            "distanceKmFromAirport": 5.5,
            "pricePerNight": 160,
            "amenities": ["wifi"],
            "cancellationPolicy": "24h",
            "paymentOptions": ["Online"],
            "roomOccupancyMax": 3,
            "imageUrl": None,
        },
        {
            "id": "C",
            "name": "Budget Stay",
            "city": "Mississauga",
            "stars": 2,
            "rating": 4.0,
            "reviewsCount": 25,
            "distanceKmFromAirport": 7.8,
            "pricePerNight": 99,
            "amenities": [],
            "cancellationPolicy": "Any",
            "paymentOptions": ["In-person"],
            "roomOccupancyMax": 2,
            "imageUrl": None,
        },
        {
            "id": "D",
            "name": "Core Downtown",
            "city": "Toronto",
            "stars": 4,
            "rating": 4.5,
            "reviewsCount": 950,
            "distanceKmFromAirport": 22.0,
            "pricePerNight": 210,
            "amenities": ["wifi", "pool", "gym", "spa", "parking"],
            "cancellationPolicy": "48h",
            "paymentOptions": ["Online", "In-person"],
            "roomOccupancyMax": 4,
            "imageUrl": None,
        },
        {
            "id": "E",
            "name": "Pearson Suites",
            "city": "Mississauga",
            "stars": 4,
            "rating": 4.5,
            "reviewsCount": 50,
            "distanceKmFromAirport": 2.0,
            "pricePerNight": 160,
            "amenities": ["wifi", "gym", "parking"],
            "cancellationPolicy": "Free",
            "paymentOptions": ["Online", "In-person"],
            "roomOccupancyMax": 2,
            "imageUrl": None,
        },
    ]


@pytest.fixture
def engine(sample_hotels, monkeypatch):
    eng = hse.HotelSearchEngine()
    # overwrite the JSON data with our in-memory dataset
    monkeypatch.setattr(eng, "data", sample_hotels, raising=True)
    return eng


def test_filter_basic_location_rating_budget(engine):
    engine.set_location("Mississauga")
    engine.set_budget(100, 170)
    engine.set_rating(3.8)
    out = engine.search()
    assert all(h["city"] == "Mississauga" for h in out)
    assert all(h["rating"] >= 3.8 for h in out)
    assert all(100 <= h["pricePerNight"] <= 170 for h in out)


def test_filter_travellers_occupancy(engine):
    engine.set_location("Mississauga")
    engine.set_budget(0, 9999)
    engine.set_travellers(3)
    out = engine.search()
    assert out and all(h.get("roomOccupancyMax", 0) >= 3 for h in out)


def test_filter_cancellation_strict(engine):
    engine.set_location("Mississauga")
    engine.set_budget(0, 9999)
    engine.set_cancellation("Free")
    out = engine.search()
    assert out and all(h.get("cancellationPolicy") == "Free" for h in out)


def test_filter_payment_inclusion(engine):
    engine.set_location("Mississauga")
    engine.set_budget(0, 9999)
    engine.set_payment("Online")
    out = engine.search()
    assert out and all("Online" in h.get("paymentOptions", []) for h in out)


def test_sort_priority_chain(engine):
    engine.set_location("Mississauga")
    engine.set_budget(0, 9999)
    out = engine.search()
    prices = [h["pricePerNight"] for h in out]
    assert prices == sorted(prices), "Primary sort must be price ASC"


def test_sort_is_stable_on_equal_keys(engine, sample_hotels, monkeypatch):
    dup1 = dict(sample_hotels[0], id="X", pricePerNight=150, rating=4.0, reviewsCount=500,
                amenities=["wifi"], distanceKmFromAirport=3.0)
    dup2 = dict(sample_hotels[0], id="Y", pricePerNight=150, rating=4.0, reviewsCount=500,
                amenities=["wifi"], distanceKmFromAirport=3.0)
    monkeypatch.setattr(engine, "data", [dup1, dup2], raising=True)
    engine.set_location(dup1["city"])
    engine.set_budget(0, 9999)
    out = engine.search()
    ids = [h["id"] for h in out]
    assert ids == ["X", "Y"], "Python sort is stable; X should keep its relative order before Y"
