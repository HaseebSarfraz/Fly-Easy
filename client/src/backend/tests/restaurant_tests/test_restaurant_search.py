import pytest
import sys, pathlib

# Ensure current backend dir is importable (robust even if run from project root)
BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]  # .../client/src/backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import restaurant_search_engine as rse

sample_restaurants = [
  {
    "id": "1",
    "name": "The Waffle Hub",
    "airport": "JFK",
    "terminal": 2,
    "category": "breakfast",
    "cuisine": "european",
    "distance": [
      0.5,
      0.7,
      0.6
    ],
    "food_type": "vegetarian",
    "hours": "05:00-11:00",
    "rating": 4.1,
    "prep_time": 6.0,
    "avg_meal_cost": 10.50,
    "review_count": 1800,
    "link": "https://img.freepik.com/premium-vector/waffle-house-logo_5555-11.jpg"
  },
  {
    "id": "2",
    "name": "Halal Burger Stop",
    "airport": "LAX",
    "terminal": 3,
    "category": "fast food",
    "cuisine": "american",
    "distance": [
      3.2,
      2.9,
      3.5
    ],
    "food_type": "halal",
    "hours": "11:00-21:00",
    "rating": 3.9,
    "prep_time": 8.0,
    "avg_meal_cost": 14.75,
    "review_count": 1220,
    "link": "https://img.freepik.com/premium-vector/burger-house-logo_1234-56.jpg"
  },
  {
    "id": "3",
    "name": "Spice Bowl Express",
    "airport": "LAX",
    "terminal": 1,
    "category": "lunch",
    "cuisine": "indian",
    "distance": [
      1.1,
      1.3,
      0.9
    ],
    "food_type": "vegan",
    "hours": "12:00-23:00",
    "rating": 4.8,
    "prep_time": 20.0,
    "avg_meal_cost": 18.00,
    "review_count": 1560,
    "link": "https://img.freepik.com/premium-vector/indian-restaurant-logo_4567-89.jpg"
  },
  {
    "id": "4",
    "name": "Skyview Tavern",
    "airport": "LHR",
    "terminal": 1,
    "category": "alcohol",
    "cuisine": "european",
    "distance": [
      0.8,
      1.0,
      1.2
    ],
    "food_type": "vegetarian",
    "hours": "07:00-01:00",
    "rating": 4.3,
    "prep_time": 5.0,
    "avg_meal_cost": 11.50,
    "review_count": 2105,
    "link": "https://img.freepik.com/premium-vector/pub-and-bar-logo_9876-54.jpg"
  },
  {
    "id": "5",
    "name": "Noodle Star",
    "airport": "LHR",
    "terminal": 3,
    "category": "dinner",
    "cuisine": "chinese",
    "distance": [
      0.9,
      1.1,
      0.8
    ],
    "food_type": "halal",
    "hours": "17:00-23:00",
    "rating": 3.7,
    "prep_time": 7.5,
    "avg_meal_cost": 12.50,
    "review_count": 2890,
    "link": "https://img.freepik.com/premium-vector/chinese-takeout-logo_4455-66.jpg"
  },
  {
    "id": "6",
    "name": "Espresso Pitstop",
    "airport": "JFK",
    "terminal": 1,
    "category": "cafe",
    "cuisine": "european",
    "distance": [
      2.0,
      2.3,
      1.9
    ],
    "food_type": "vegan",
    "hours": "06:00-20:00",
    "rating": 4.2,
    "prep_time": 4.0,
    "avg_meal_cost": 7.50,
    "review_count": 1950,
    "link": "https://img.freepik.com/premium-vector/coffee-shop-logo_8765-12.jpg"
  },
  {
    "id": "7",
    "name": "Ramen Run",
    "airport": "ATL",
    "terminal": 2,
    "category": "fast food",
    "cuisine": "japanese",
    "distance": [
      0.4,
      0.5,
      0.3
    ],
    "food_type": "vegetarian",
    "hours": "08:00-00:00",
    "rating": 4.0,
    "prep_time": 9.0,
    "avg_meal_cost": 15.00,
    "review_count": 1400,
    "link": "https://img.freepik.com/premium-vector/sushi-bar-logo_7088-34.jpg"
  },
  {
    "id": "8",
    "name": "Chai & Samosas",
    "airport": "ATL",
    "terminal": 3,
    "category": "cafe",
    "cuisine": "indian",
    "distance": [
      1.8,
      1.6,
      2.0
    ],
    "food_type": "vegan",
    "hours": "07:30-19:30",
    "rating": 4.4,
    "prep_time": 10.0,
    "avg_meal_cost": 8.00,
    "review_count": 1050,
    "link": "https://img.freepik.com/premium-vector/indian-tea-logo_5566-77.jpg"
  },
  {
    "id": "9",
    "name": "All-American Grill",
    "airport": "ORD",
    "terminal": 2,
    "category": "dinner",
    "cuisine": "american",
    "distance": [
      2.5,
      2.8,
      2.6
    ],
    "food_type": "halal",
    "hours": "16:00-22:00",
    "rating": 4.7,
    "prep_time": 25.0,
    "avg_meal_cost": 28.50,
    "review_count": 910,
    "link": "https://img.freepik.com/premium-vector/american-diner-logo_3344-55.jpg"
  },
  {
    "id": "10",
    "name": "The Gate Bar",
    "airport": "ORD",
    "terminal": 1,
    "category": "alcohol",
    "cuisine": "european",
    "distance": [
      0.1,
      0.2,
      0.1
    ],
    "food_type": "vegetarian",
    "hours": "10:00-23:00",
    "rating": 4.6,
    "prep_time": 5.0,
    "avg_meal_cost": 9.99,
    "review_count": 3100,
    "link": "https://img.freepik.com/premium-vector/bar-lounge-logo_6677-88.jpg"
  },
  {
    "id": "11",
    "name": "The Bagel Stop",
    "airport": "JFK",
    "terminal": 3,
    "category": "breakfast",
    "cuisine": "american",
    "distance": [
      1.4,
      1.6,
      1.2
    ],
    "food_type": "vegan",
    "hours": "05:30-10:30",
    "rating": 4.0,
    "prep_time": 4.5,
    "avg_meal_cost": 6.88,
    "review_count": 1487,
    "link": "https://img.freepik.com/premium-vector/bagel-restaurant-logo_9975-3.jpg"
  },
  {
    "id": "12",
    "name": "Tokyo Express",
    "airport": "LAX",
    "terminal": 2,
    "category": "fast food",
    "cuisine": "japanese",
    "distance": [
      1.2,
      1.5,
      1.1
    ],
    "food_type": "vegetarian",
    "hours": "10:00-22:00",
    "rating": 4.2,
    "prep_time": 10.0,
    "avg_meal_cost": 17.50,
    "review_count": 1350,
    "link": "https://img.freepik.com/premium-vector/japanese-fast-food-logo_1122-33.jpg"
  },
  {
    "id": "13",
    "name": "Curry Corner",
    "airport": "LHR",
    "terminal": 2,
    "category": "lunch",
    "cuisine": "indian",
    "distance": [
      2.0,
      1.9,
      2.2
    ],
    "food_type": "halal",
    "hours": "11:30-15:30",
    "rating": 4.5,
    "prep_time": 18.0,
    "avg_meal_cost": 21.00,
    "review_count": 850,
    "link": "https://img.freepik.com/premium-vector/curry-restaurant-logo_4455-66.jpg"
  },
  {
    "id": "14",
    "name": "Blue Sky Bistro",
    "airport": "ATL",
    "terminal": 1,
    "category": "dinner",
    "cuisine": "european",
    "distance": [
      3.0,
      3.1,
      2.9
    ],
    "food_type": "vegetarian",
    "hours": "17:00-23:00",
    "rating": 4.9,
    "prep_time": 30.0,
    "avg_meal_cost": 32.00,
    "review_count": 750,
    "link": "https://img.freepik.com/premium-vector/bistro-restaurant-logo_9988-77.jpg"
  },
  {
    "id": "15",
    "name": "The Tarmac Tap",
    "airport": "ATL",
    "terminal": 3,
    "category": "alcohol",
    "cuisine": "american",
    "distance": [
      0.6,
      0.8,
      0.7
    ],
    "food_type": "vegan",
    "hours": "10:00-01:00",
    "rating": 4.3,
    "prep_time": 5.0,
    "avg_meal_cost": 10.99,
    "review_count": 2500,
    "link": "https://img.freepik.com/premium-vector/taproom-logo_1212-34.jpg"
  },
  {
    "id": "16",
    "name": "Morning Glory Cafe",
    "airport": "ORD",
    "terminal": 3,
    "category": "cafe",
    "cuisine": "european",
    "distance": [
      1.0,
      1.1,
      1.3
    ],
    "food_type": "vegetarian",
    "hours": "04:00-14:00",
    "rating": 3.8,
    "prep_time": 5.5,
    "avg_meal_cost": 9.50,
    "review_count": 2200,
    "link": "https://img.freepik.com/premium-vector/cafe-and-bakery-logo_3456-78.jpg"
  },
  {
    "id": "17",
    "name": "Great Wall Wok",
    "airport": "JFK",
    "terminal": 2,
    "category": "fast food",
    "cuisine": "chinese",
    "distance": [
      0.7,
      0.9,
      0.8
    ],
    "food_type": "halal",
    "hours": "11:00-20:00",
    "rating": 4.1,
    "prep_time": 7.0,
    "avg_meal_cost": 13.00,
    "review_count": 1650,
    "link": "https://img.freepik.com/premium-vector/chinese-restaurant-logo_6677-88.jpg"
  },
  {
    "id": "18",
    "name": "Sake Bar",
    "airport": "LAX",
    "terminal": 1,
    "category": "alcohol",
    "cuisine": "japanese",
    "distance": [
      0.3,
      0.4,
      0.5
    ],
    "food_type": "vegan",
    "hours": "12:00-23:00",
    "rating": 4.7,
    "prep_time": 3.0,
    "avg_meal_cost": 18.99,
    "review_count": 1100,
    "link": "https://img.freepik.com/premium-vector/japanese-bar-logo_9988-77.jpg"
  },
  {
    "id": "19",
    "name": "The Runway Diner",
    "airport": "LHR",
    "terminal": 3,
    "category": "dinner",
    "cuisine": "american",
    "distance": [
      1.5,
      1.4,
      1.6
    ],
    "food_type": "halal",
    "hours": "16:30-22:30",
    "rating": 4.0,
    "prep_time": 22.0,
    "avg_meal_cost": 24.99,
    "review_count": 950,
    "link": "https://img.freepik.com/premium-vector/diner-restaurant-logo_1122-44.jpg"
  },
  {
    "id": "20",
    "name": "Oriental Tea House",
    "airport": "ORD",
    "terminal": 2,
    "category": "cafe",
    "cuisine": "chinese",
    "distance": [
      2.4,
      2.6,
      2.3
    ],
    "food_type": "vegetarian",
    "hours": "07:00-19:00",
    "rating": 4.2,
    "prep_time": 6.5,
    "avg_meal_cost": 8.50,
    "review_count": 1750,
    "link": "https://img.freepik.com/premium-vector/tea-house-logo_5544-66.jpg"
  },
{
    "id": "21",
    "name": "The Waffle Hub",
    "airport": "JFK",
    "terminal": 3,
    "category": "breakfast",
    "cuisine": "european",
    "distance": [
      0.4,
      0.6,
      0.5
    ],
    "food_type": "vegetarian",
    "hours": "05:00-11:00",
    "rating": 4.0,
    "prep_time": 6.5,
    "avg_meal_cost": 10.50,
    "review_count": 1500,
    "link": "https://img.freepik.com/premium-vector/waffle-house-logo_5555-11.jpg"
  },
  {
    "id": "22",
    "name": "The Bagel Stop",
    "airport": "JFK",
    "terminal": 1,
    "category": "fast food",
    "cuisine": "american",
    "distance": [
      1.0,
      1.2,
      0.8
    ],
    "food_type": "vegan",
    "hours": "06:00-11:00",
    "rating": 4.1,
    "prep_time": 5.0,
    "avg_meal_cost": 7.00,
    "review_count": 1350,
    "link": "https://img.freepik.com/premium-vector/bagel-restaurant-logo_9975-3.jpg"
  }
]


@pytest.fixture()
def engine(monkeypatch):
    """
    Sets up the search engine for the restaurants.
    """
    res_eng = rse.RestaurantSearchEngine()
    # overwrite the JSON data with our in-memory dataset
    monkeypatch.setattr(res_eng, "restaurants", sample_restaurants, raising=True)
    return res_eng


def test_sort_by_price(engine):
    """
    Tests whether the returned restaurants at the airport are sorted by increasing
    and decreasing average meal cost.
    """
    engine.set_location("LAX", 2)
    engine.set_sort_price(1)
    result = engine.find_restaurants()
    assert [r["avg_meal_cost"] for r in result] == sorted([r["avg_meal_cost"] for r in result])

    engine.set_sort_price(-1)
    result = engine.find_restaurants()
    assert [r["avg_meal_cost"] for r in result] == sorted([r["avg_meal_cost"] for r in result], reverse=True)


def test_filter_by_budget(engine):
    """
    Tests whether the returned restaurants at the airport are filtered by food type that can be offered.
    """
    engine.set_location("JFK", 1)
    result = engine.find_restaurants()
    engine.set_budget(15)
    assert max([r["avg_meal_cost"] for r in result]) == 13

    engine.set_budget(10)
    result = engine.find_restaurants()
    assert max([r["avg_meal_cost"] for r in result]) == 7.5


def test_filter_by_prep_time(engine):
    """
    Tests whether the correct restaurant was returned with an estimated wait time within the customer's
    patience level.
    """
    engine.set_location("ATL", 2)
    engine.set_max_prep_time(10)
    result = engine.find_restaurants()

    assert len(result) == 3
    restaurant_list = [r for r in result]
    wait_times = [r["prep_time"] for r in result]
    assert restaurant_list[wait_times.index(max(wait_times))]["name"] == "Chai & Samosas"
    assert max(wait_times) == 10


def test_filter_by_rating(engine):
    """
    Tests the correct returned restaurants with atleast the minimum specified rating.
    """
    engine.set_location("LHR", 1)
    engine.set_min_rating(4)
    result = engine.find_restaurants()
    assert len(result) == 3
    assert min([r["rating"] for r in result]) == 4.0

    engine.set_min_rating(0)
    result = engine.find_restaurants()
    assert len(result) == 4
    assert min([r["rating"] for r in result]) == 3.7


def test_filter_by_distance(engine):
    """
    Tests the correct returned restaurants within the mentioned distance.
    """
    engine.set_location("LHR", 1)
    engine.set_distance(1)
    result = engine.find_restaurants()
    assert len(result) == 2
    assert max([r["distance"] for r in result]) == 0.9

    engine.set_distance(2)
    result = engine.find_restaurants()
    assert len(result) == 4
    assert max([r["distance"] for r in result]) == 2


def test_filter_by_food_type(engine):
    """
    Tests the restaurants filtered based on specified restaurant type.
    """
    engine.set_location("ORD", 1)
    engine.set_food_category("alcohol")
    result = engine.find_restaurants()
    assert len(result) == 1
    assert result[0]["name"] == "The Gate Bar"

def test_specified_restaurant(engine):
    """
    Tests whether the correct restaurants are returned based on the specified name.
    """
    engine.set_location("JFK", 2)
    engine.set_restaurant("The Bagel Stop")
    result = engine.find_restaurants()
    assert [r["name"] for r in result] == ["The Bagel Stop", "The Bagel Stop"]


def test_filter_by_cuisine(engine):
    """
    Tests the restaurants fetched based on the specified cuisine.
    """
    engine.set_location("JFK", 1)
    engine.set_cuisine("european")
    result = engine.find_restaurants()
    assert len(result) == 3

    engine.set_location("LHR", 1)
    engine.set_cuisine("european")
    result.extend(engine.find_restaurants())
    assert len(result) == 4

    engine.set_location("ORD", 1)
    engine.set_cuisine("european")
    result.extend(engine.find_restaurants())
    assert len(result) == 6
