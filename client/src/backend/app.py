# client/src/backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from hotel_search_engine import HotelSearchEngine
from RestaurantSearchEngine import RestaurantSearchEngine

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

if __name__ == "__main__":
    print("Starting Flask on http://0.0.0.0:5001 …")
    app.run(host="0.0.0.0", port=5001, debug=True)
