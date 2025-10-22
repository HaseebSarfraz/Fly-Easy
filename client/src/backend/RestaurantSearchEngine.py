import datetime
import json
from typing import Optional


class RestaurantSearchEngine:
    """
    A class representing the search restaurant for a restaurant.
    """
    current_location: tuple[Optional[str], Optional[int]]

    def __init__(self):
        with open("RestaurantSearchAndFilter.py") as r:
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
        self.sort_price = "asc"
        self.sort_distance = "asc"
        self.sort_prep_time = "asc"
        self.sort_rating = "desc"

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
        self.sort_price = None
        if sort_by != "none":
            self.sort_price = sort_by

    def set_sort_dist(self, sort_by: str) -> None:
        self.sort_distance = None
        if sort_by != "none":
            self.sort_distance = sort_by

    def set_sort_rating(self, sort_by: str) -> None:
        self.sort_rating = None
        if sort_by != "none":
            self.sort_rating = sort_by

    def set_sort_prep_time(self, sort_by: str) -> None:
        self.sort_prep_time = None
        if sort_by != "none":
            self.sort_prep_time = sort_by

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
            filtered_restaurants = []
            main_restaurants = []
            user_search_info = self.current_location[0] + self.food_category + self.cuisine + self.diet_restriction
            for restaurant in self.restaurants:
                restaurant_info = (restaurant["airport"], restaurant["category"], restaurant["cuisine"],
                                   restaurant["food_type"])
                if ((user_search_info[3] is None and user_search_info[:3] == restaurant_info[:3])
                        or (user_search_info[3] is not None and user_search_info == restaurant_info)):
                    main_restaurants.append(restaurant)

            if main_restaurants:
                for restaurant in main_restaurants:
                    hours = restaurant["hours"].split("-")
                    opening_time = hours[0]
                    closing_time = hours[1]

                    open_time = datetime.datetime.strptime(opening_time, "%H:%M").time()
                    close_time = datetime.datetime.strptime(closing_time, "%H:%M").time()

                    if self.restaurant_name is None or self.restaurant_name == restaurant["name"]:
                        if self.max_distance is None or int(restaurant["distance"][self.current_location[1] - 1]) <= self.max_distance:
                            if self.max_prep_time is None or float(restaurant["prep_time"]) <= self.max_distance:
                                if self.min_rating is None or float(restaurant["rating"]) >= self.min_rating:
                                    if self.budget is None or float(restaurant["cheapest_item"]) >= self.budget:
                                        if (self.wants_open_now and open_time <= self.time <= close_time) or not self.wants_open_now:
                                            filtered_restaurants.append(restaurant)

            if filtered_restaurants:
                if self.sort_price:
                    if self.sor

        except IndexError:
            return []


    def _bayesian_review_weight(self, rating: float, reviews: int, prior: float = 3.9, m: int = 150) -> float:
        # Higher reviews pull the score toward the true rating; low-review items get pulled toward the prior.
        v = max(0, int(reviews))
        return (v / (v + m)) * float(rating) + (m / (v + m)) * float(prior)
