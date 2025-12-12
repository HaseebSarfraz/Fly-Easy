# src/planner/core/food_filter.py
from typing import List, Dict

CUISINE_KEYWORDS = {
    "italian": ["italian", "pizza", "pasta", "trattoria"],
    "turkish": ["turkish", "doner", "kebab"],
    "southasian": ["pakistani", "indian", "bangladeshi", "desi", "biryani", "tandoori"],
    "american": ["american", "burger", "bbq", "diner"],
    "japanese": ["japanese", "sushi", "ramen"],
    "middle_eastern": ["middle eastern", "lebanese", "shawarma"],
    # extend as needed
}

AVOID_KEYWORDS = {
    "pork": ["pork", "charcuterie"],
    "alcohol_forward": ["bar", "pub", "brewery", "wine"],
    # etc.
}

def cuisine_query(cuisine_likes: List[str]):
    tokens = []
    for c in cuisine_likes:
        tokens += CUISINE_KEYWORDS.get(c.lower(), [c])
    return " ".join(tokens) if tokens else None

def violates_avoid(place: dict, avoid_terms: List[str]) -> bool:
    text = " ".join([
        place.get("name",""),
        place.get("vicinity",""),
        " ".join(place.get("types", []))
    ]).lower()
    bad_words = []
    for a in avoid_terms:
        bad_words += AVOID_KEYWORDS.get(a.lower(), [a])
    return any(term in text for term in bad_words)