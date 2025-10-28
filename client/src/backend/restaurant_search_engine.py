import copy
import datetime
import json
from typing import Optional
import os


class RestaurantSearchEngine:
    """
    A class representing the search restaurant for a restaurant.
    """
    current_location: tuple[Optional[str], Optional[int]]
    food_category: Optional[str]
    cuisine: Optional[str]
    diet_restriction: Optional[str]

    def __init__(self):
        file_path = os.path.join(os.path.dirname(__file__), "data", "airport_restaurants_mock.json")

        with open(file_path, encoding="utf-8") as r:
            self.restaurants = json.load(r)

        # 1. PRIMARY SEARCH PARAMETERS ON THE FIRST SCREEN
        self.current_location = (None, None)  # FORMAT: (AIRPORT, TERMINAL)
        self.food_category = None
        self.cuisine = None
        self.diet_restriction = None
        # 2. SECONDARY SEARCH PARAMETERS ON THE SECOND SCREEN
        self.restaurant_name = None
        self.max_distance = 0
        self.max_prep_time = 0
        self.min_rating = 0
        self.budget = 0
        self.wants_open_now = False
        # 3. SORTING PARAMETERS
        self.sort_price = 1
        self.sort_distance = 1
        self.sort_prep_time = 1
        self.sort_rating = -1

        # USED FOR SEARCHING RESTAURANTS THAT ARE CURRENTLY OPEN
        self.time = datetime.datetime.now().time()

    # PRIMARY SEARCH PAGE SETTERS
    def set_location(self, airport: str, terminal: int) -> None:
        """
        Sets the location for the user.
        """
        self.current_location = airport, terminal

    def set_food_category(self, category: str) -> None:
        """
        Sets the food category selected by user.
        """
        self.food_category = category

    def set_cuisine(self, cuisine: str) -> None:
        """
        Sets the cuisine preferred by the user.
        """
        self.cuisine = cuisine

    def set_restrictions(self, restriction: str) -> None:
        """
        Sets the dietary restrictions by the user.
        """
        self.diet_restriction = restriction

    def set_distance(self, distance: int) -> None:
        """
        Sets the restaurant budget.
        """
        self.max_distance = distance

    # SECONDARY SEARCH PAGE SETTERS
    def set_restaurant(self, name: str) -> None:
        """
        Sets the preferred restaurant.
        """
        self.restaurant_name = None
        name = name.strip().lower()
        print(name)
        if name:
            self.restaurant_name = name

    def set_max_prep_time(self, prep_time: int) -> None:
        """
        Sets the maximum prep time for the food.
        """
        self.max_prep_time = prep_time

    def set_min_rating(self, rating: int) -> None:
        """
        Sets the minimum rating for the restaurants.
        """
        self.min_rating = rating

    def set_budget(self, budget: int) -> None:
        """
        Sets the max budget for the search.
        """
        self.budget = budget

    def toggle_wants_open_now(self, wants_open: bool):
        self.wants_open_now = wants_open

    def set_sort_price(self, sort_by: int) -> None:
        self.sort_price = sort_by

    def set_sort_dist(self, sort_by: int) -> None:
        self.sort_distance = sort_by

    def set_sort_rating(self, sort_by: int) -> None:
        self.sort_rating = sort_by

    def set_sort_prep_time(self, sort_by: int) -> None:
        self.sort_prep_time = sort_by

    def find_restaurants(self) -> list:
        try:
            filtered_restaurants = []
            main_restaurants = []
            user_search_info = self.current_location[0], self.food_category, self.cuisine, self.diet_restriction
            for restaurant in self.restaurants:
                matches = True
                restaurant_info = (restaurant["airport"], restaurant["category"], restaurant["cuisine"],
                                   restaurant["food_type"])

                if user_search_info[0] == restaurant_info[0]:
                    for i in range(1, 4):
                        if user_search_info[i] and user_search_info[i] != restaurant_info[i]:
                            matches = False
                            break
                    if matches:
                        main_restaurants.append(restaurant)

            if main_restaurants:
                for restaurant in main_restaurants:
                    hours = restaurant["hours"].split("-")
                    opening_time = hours[0]
                    closing_time = hours[1]

                    open_time = datetime.datetime.strptime(opening_time, "%H:%M").time()
                    close_time = datetime.datetime.strptime(closing_time, "%H:%M").time()
                    r_dict = copy.copy(restaurant)
                    r_dict["distance"] = r_dict["distance"][self.current_location[1] - 1]
                    if self.restaurant_name is None or self.restaurant_name == restaurant["name"].lower():
                        if self.max_distance == 0 or float(r_dict["distance"]) <= self.max_distance:
                            if self.max_prep_time == 0 or float(r_dict["prep_time"]) <= self.max_prep_time:
                                if self.min_rating == 0 or float(r_dict["rating"]) >= self.min_rating:
                                    if self.budget == 0 or float(r_dict["avg_meal_cost"]) <= self.budget:
                                        if ((self.wants_open_now and open_time <= self.time <= close_time) or
                                                not self.wants_open_now):
                                            hours = r_dict.pop("hours").split("-")
                                            r_dict["open_time"], r_dict["close_time"] = hours[0], hours[1]
                                            r_dict["open_now"] = open_time <= self.time <= close_time
                                            filtered_restaurants.append(r_dict)
                filtered_restaurants.sort(key=self._rank_key)
                return filtered_restaurants
        except IndexError:
            return []

    def _rank_key(self, r):
        # 1) price in ascending order
        price = r["avg_meal_cost"] * self.sort_price

        # 2) review weight (descending) via negative sign)
        rating = r["rating"]
        reviews = r["review_count"]
        review_weight = bayesian_review_weight(rating, reviews)

        # 3) food prep time
        prep_time = r["prep_time"] * self.sort_prep_time

        # 4) distance (asc)
        dist = r["distance"] * self.sort_distance

        # Tuple order enforces priorities; negate where we want descending
        return price, review_weight * self.sort_rating, prep_time, dist
    

def bayesian_review_weight(rating: float, reviews: int, prior: float = 3.9, m: int = 150) -> float:
    # Higher reviews pull the score toward the true rating; low-review items get pulled toward the prior.
    v = max(0, int(reviews))
    return (v / (v + m)) * float(rating) + (m / (v + m)) * float(prior)


if __name__ == "__main__":
    eng = RestaurantSearchEngine()
    eng.set_location("YYZ", 1)
    eng.set_restaurant("Panda Express")
    # eng.set_food_category("lunch")    # UNCOMMENT THESE ONE BY ONE FOR THE DEMO
    # eng.set_min_rating("2")
    # eng.set_distance("2")
    # eng.set_cuisine("american")
    # eng.set_sort_dist("asc")
    # eng.set_sort_prep_time("asc")
    eng.toggle_wants_open_now(True)
    results = eng.find_restaurants()  # NOTE, SORTING IS NOT DONE YET
    print("sorting options:")
    print("price = " + ("increasing" if eng.sort_price == 1 else "decreasing").upper())
    print("rating = " + ("increasing" if eng.sort_rating  == 1 else "decreasing").upper())
    print("prep time = " + ("increasing" if eng.sort_prep_time == 1 else "decreasing").upper())
    print("distance = " + ("increasing" if eng.sort_distance == 1 else "decreasing").upper())

    if not results:
        print("No such restaurants")
    else:
        print(f"\nFOUND {len(results)} RESTAURANTS")
        for h in results:
            print("\nRestaurant: " + h["name"] +
                  "\nRestaurant cheapest item price: $" + str(h["avg_meal_cost"]) +
                  "\nRestaurant rating: " + str(h["rating"]) +
                  "\nRestaurant food prep time: " + str(h["prep_time"]) +
                  "\nRestaurant distance from you: " + str(h["distance"])
                  # "\nRestaurant hours: " + h["hours"])
                  )
