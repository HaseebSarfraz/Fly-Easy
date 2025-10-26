import copy
import datetime
import json
from typing import Optional
import os
from flask import Flask


class RestaurantSearchEngine:
    """
    A class representing the search restaurant for a restaurant.
    """
    current_location: tuple[Optional[str], Optional[int]]

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
        self.max_distance = None
        self.max_prep_time = None
        self.min_rating = 0
        self.budget = None
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
        self.food_category = None
        if category != "any":
            self.food_category = category

    def set_cuisine(self, cuisine: str) -> None:
        """
        Sets the cuisine preferred by the user.
        """
        self.cuisine = None
        if cuisine != "any":
            self.cuisine = cuisine

    def set_restrictions(self, restriction: str) -> None:
        """
        Sets the dietary restrictions by the user.
        """
        self.diet_restriction = None
        if restriction != "none":
            self.diet_restriction = restriction

    def set_distance(self, distance: str) -> None:
        """
        Sets the restaurant budget.
        """
        self.max_distance = None
        if distance != "any":
            self.max_distance = int(distance)

    # SECONDARY SEARCH PAGE SETTERS
    def set_restaurant(self, name: str) -> None:
        """
        Sets the preferred restaurant.
        """
        self.restaurant_name = None
        name = name.strip().lower()
        if name:
            self.restaurant_name = name

    def set_max_prep_time(self, prep_time: str) -> None:
        """
        Sets the maximum prep time for the food.
        """
        self.max_prep_time = None
        if prep_time != "any":
            self.max_prep_time = int(prep_time)

    def set_min_rating(self, rating: str) -> None:
        """
        Sets the minimum rating for the restaurants.
        """
        self.min_rating = 0
        if rating != "any":
            self.min_rating = int(rating)

    def set_budget(self, budget: str) -> None:
        """
        Sets the max budget for the search.
        """
        self.budget = None
        if budget != "any":
            self.budget = int(budget)

    def toggle_wants_open_now(self):
        self.wants_open_now = not self.wants_open_now

    def set_sort_price(self, sort_by: str) -> None:
        self.sort_price = 1 if sort_by in ["asc", "none"] else -1

    def set_sort_dist(self, sort_by: str) -> None:
        self.sort_distance = 1 if sort_by in ["asc", "none"] else -1

    def set_sort_rating(self, sort_by: str) -> None:
        self.sort_rating = 1 if sort_by in ["asc", "none"] else -1

    def set_sort_prep_time(self, sort_by: str) -> None:
        self.sort_prep_time = 1 if sort_by in ["asc", "none"] else -1

    def search_restaurants(self) -> list:
        result = []
        user_search_info = self.current_location[0] + self.food_category + self.cuisine + self.diet_restriction
        for restaurant in self.restaurants:
            restaurant_info = (restaurant["airport"], restaurant["category"], restaurant["cuisine"],
                               restaurant["food_type"])
            if ((user_search_info[3] is None and user_search_info[:3] == restaurant_info[:3])
                    or (user_search_info[3] is not None and user_search_info == restaurant_info)):
                result.append(restaurant)
        return result

    def filter_and_sort_restaurants(self) -> list:
        try:
            restaurant_groupings = {}
            sorted_restaurants = []
            filtered_restaurants = []
            main_restaurants = []
            user_search_info = self.current_location[0], self.food_category, self.cuisine, self.diet_restriction
            for restaurant in self.restaurants:
                restaurant_info = (restaurant["airport"], restaurant["category"], restaurant["cuisine"],
                                   restaurant["food_type"])

                if user_search_info[0] == restaurant_info[0]:
                    for i in range(1, 4):
                        if user_search_info[i] and user_search_info[i] != restaurant_info[i]:
                            break
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
                    if self.restaurant_name is None or self.restaurant_name == restaurant["name"]:
                        if self.max_distance is None or float(r_dict["distance"]) <= self.max_distance:
                            if self.max_prep_time is None or float(r_dict["prep_time"]) <= self.max_prep_time:
                                if self.min_rating is None or float(r_dict["rating"]) >= self.min_rating:
                                    if self.budget is None or float(r_dict["cheapest_item"]) >= self.budget:
                                        if ((self.wants_open_now and open_time <= self.time <= close_time) or
                                                not self.wants_open_now):
                                            filtered_restaurants.append(r_dict)
                filtered_restaurants.sort(key=self._rank_key)
                return filtered_restaurants
        except IndexError:
            return []

    def _rank_key(self, r):
        # 1) price in ascending order
        price = r["cheapest_item"] * self.sort_price

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
    eng.set_location("CDG", 2)
    # eng.set_food_category("lunch")    # UNCOMMENT THESE ONE BY ONE FOR THE DEMO
    # eng.set_min_rating("2")
    # eng.set_distance("2")
    # eng.set_cuisine("american")
    # eng.set_sort_dist("asc")
    # eng.set_sort_prep_time("asc")
    eng.toggle_wants_open_now()
    results = eng.filter_and_sort_restaurants()  # NOTE, SORTING IS NOT DONE YET
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
                  "\nRestaurant cheapest item price: $" + str(h["cheapest_item"]) +
                  "\nRestaurant rating: " + str(h["rating"]) +
                  "\nRestaurant food prep time: " + str(h["prep_time"]) +
                  "\nRestaurant distance from you: " + str(h["distance"])
                  # "\nRestaurant hours: " + h["hours"])
                  )
