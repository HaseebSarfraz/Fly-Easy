// HotelResultsScreen.tsx
import React, { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, FlatList, Text, View } from "react-native";
import HotelResultCard from "../../components/hotel-components/HotelResultCard";
import { diffNights, overallScore } from "../../utils/hotels";

type Hotel = {
  id: string;
  name: string;
  city: string;
  stars?: number;
  rating?: number;                  // 0–5
  reviewsCount?: number;
  distanceKmFromAirport?: number | null;
  pricePerNight: number;
  amenities: string[];
  imageUrl?: string | null;
  thumbnailUrl?: string | null;
};

export default function HotelResultsScreen({ route, navigation }: any) {
    const {
    location = "",
    travellers = 1,
    checkIn = "",
    checkOut = "",
    budgetMin,
    budgetMax,
    minRating,
    cancellation,
    payment,
    } = route?.params ?? {};

  const [rows, setRows] = useState<Hotel[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const nights = useMemo(() => diffNights(checkIn, checkOut), [checkIn, checkOut]);

  useEffect(() => {
    (async () => {
      try {
        setErr(null); setRows(null);
        const res = await fetch("http://127.0.0.1:5001/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ location, travellers, minRating, cancellation, payment, budgetMin, budgetMax })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: Hotel[] = await res.json();
        setRows(data);
      } catch (e: any) { setErr(e.message); }
    })();
  }, [location, travellers, minRating, cancellation, payment, budgetMin, budgetMax]);

  if (err) return <Text style={{ padding: 16 }}>Error: {err}</Text>;
  if (!rows) return <ActivityIndicator style={{ marginTop: 24 }} />;

  // Peer median price (for overall score)
  const median = (() => {
    const ps = rows.map(r => r.pricePerNight).sort((a,b)=>a-b);
    const mid = Math.floor(ps.length/2);
    return ps.length % 2 ? ps[mid] : (ps[mid-1]+ps[mid])/2;
  })();

  return (
    <FlatList
      contentContainerStyle={{ padding: 12 }}
      data={rows}
      keyExtractor={(h) => String(h.id)}
      renderItem={({ item }) => {
        const bullets = [
          item.amenities.includes("breakfast") && "Breakfast included",
          item.amenities.includes("free_cancellation") && "Free cancellation",
          item.amenities.includes("no_prepayment") && "No prepayment needed",
        ].filter(Boolean) as string[];

        const overall10 = overallScore({
          rating: item.rating ?? 0,
          reviewsCount: item.reviewsCount ?? 0,
          amenitiesCount: item.amenities.length,
          pricePerNight: item.pricePerNight,
          peersMedianPrice: median || item.pricePerNight
        });

        return (
          <HotelResultCard
            name={item.name}
            stars={item.stars || 0}
            rating5={item.rating}
            reviewsCount={item.reviewsCount}
            distanceKmFromAirport={item.distanceKmFromAirport ?? null}
            nights={nights}
            travellers={travellers}
            pricePerNight={item.pricePerNight}
            imageUrl={item.thumbnailUrl ?? item.imageUrl ?? undefined}
            bullets={bullets}
            overall10={overall10}
            onPress={() => { // TODO: add HotelDetails screen later
                // navigation.navigate("HotelDetails", { id: item.id });}
            }} />
        );
      }}
    />
  );
}
