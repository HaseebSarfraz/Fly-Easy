# client/src/backend/tests/hotel_tests/conftest.py
import pytest
import hotel_search_engine as hse

@pytest.fixture
def sample_hotels():
    # Keep these small but varied so filters/sorting can be exercised
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
    """Return an engine whose data is overridden to our sample list."""
    eng = hse.HotelSearchEngine()
    # Overwrite the loaded JSON with our test dataset
    monkeypatch.setattr(eng, "data", sample_hotels, raising=True)
    return eng
