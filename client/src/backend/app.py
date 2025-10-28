# client/src/backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from hotel_search_engine import HotelSearchEngine
from restaurant_search_engine import RestaurantSearchEngine

app = Flask(__name__)
CORS(app)


@app.post("/search")
def search():
    p = request.get_json(force=True) or {}
    eng = HotelSearchEngine()

    location   = p.get("location", "")
    travellers = int(p.get("travellers", 1))

    bmin = p.get("budgetMin")
    bmax = p.get("budgetMax")
    bmin = float(bmin) if bmin not in (None, "") else None
    bmax = float(bmax) if bmax not in (None, "") else None

    min_rating = p.get("minRating")
    min_rating = float(min_rating) if min_rating not in (None, "") else None

    cancellation = p.get("cancellation")
    payment      = p.get("payment")

    eng.set_location(location)
    eng.set_travellers(travellers)
    eng.set_budget(bmin, bmax)
    if min_rating is not None: eng.set_rating(min_rating)
    if cancellation: eng.set_cancellation(cancellation)
    if payment:      eng.set_payment(payment)

    return jsonify(eng.search())


@app.post("/search_restaurants")
def search_restaurants():
    p = request.get_json(force=True) or {}
    reng = RestaurantSearchEngine()
    print("Initialized restaurant search engine")

    iata = p.get("iata", "")
    terminal = int(p.get("terminal", 1))
    food_category = p.get("food_category", "any")
    cuisine = p.get("cuisine", "any")
    diet_restr = p.get("dietary_restriction", "none")

    print("Primary search params set")

    restaurant = p.get("restaurant", "")
    distance = int(p.get("max_distance", 0))
    prep_time = int(p.get("prep_time", 0))
    rating = int(p.get("min_rating", 0))
    price_sort = int(p.get("p_sort", 1))
    dist_sort = int(p.get("d_sort", 1))
    rating_sort = int(p.get("r_sort", -1))
    time_sort = int(p.get("t_sort", 1))
    wants_open = bool(p.get("wants_open", False))

    reng.set_location(iata, terminal)
    reng.set_food_category(food_category)
    reng.set_cuisine(cuisine)
    reng.set_restrictions(diet_restr)

    reng.set_restaurant(restaurant)
    reng.set_distance(distance)
    reng.set_max_prep_time(prep_time)
    reng.set_min_rating(rating)
    
    reng.set_sort_price(price_sort)
    reng.set_sort_dist(dist_sort)
    reng.set_sort_rating(rating_sort)
    reng.set_sort_prep_time(time_sort)
    reng.toggle_wants_open_now(wants_open)

    print("Secondary search params set")

    return jsonify(reng.find_restaurants())


if __name__ == "__main__":
    print("Starting Flask on http://0.0.0.0:5001 …")
    app.run(host="0.0.0.0", port=5001, debug=True)
