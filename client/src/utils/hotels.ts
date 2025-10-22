// src/utils/hotels.ts
export function parseISO(date: string) {
  const d = new Date(date);
  return isNaN(+d) ? null : d;
}

export function diffNights(checkIn: string, checkOut: string) {
  const a = parseISO(checkIn), b = parseISO(checkOut);
  if (!a || !b) return 1;
  const MS = 1000 * 60 * 60 * 24;
  const n = Math.max(1, Math.round((b.getTime() - a.getTime()) / MS));
  return n;
}

// Bayesian review weight (same as backend)
export function bayesWeight(ratingOutOf5: number, reviews: number, prior = 3.9, m = 150) {
  const v = Math.max(0, Math.floor(reviews || 0));
  const r = Number(ratingOutOf5 || 0);
  return (v / (v + m)) * r + (m / (v + m)) * prior; // returns on 0–5 scale
}

// Turn 0–5 -> 0–10 for the “Overall 8.4” badge
export function toTenScale(x0to5: number) {
  return Math.max(0, Math.min(10, (x0to5 / 5) * 10));
}

// Simple “overall” (you can later move to backend):
// overall = bayes (0–10) + amenities bonus (0..~1) − price penalty (0..~1)
export function overallScore({
  rating, reviewsCount, amenitiesCount, pricePerNight, peersMedianPrice
}: { rating: number; reviewsCount: number; amenitiesCount: number; pricePerNight: number; peersMedianPrice: number; }) {
  const bayes = toTenScale(bayesWeight(rating, reviewsCount)); // 0..10
  const amenityBonus = Math.min(1.0, (amenitiesCount / 12) * 1.0); // up to +1
  const pricePenalty = Math.max(-1.0, Math.min(1.0, (pricePerNight - peersMedianPrice) / (peersMedianPrice * 1.0)));
  // cheaper than median gives negative penalty (i.e., bonus), more expensive positive penalty
  const overall = bayes + amenityBonus - pricePenalty; // still ~0..12 → clamp to 0..10
  return Math.max(0, Math.min(10, overall));
}
