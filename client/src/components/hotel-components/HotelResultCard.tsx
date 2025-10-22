import React, { useMemo, useState } from "react";
import { View, Text, Image, Pressable } from "react-native";

type Props = {
  name: string;
  stars?: number;
  rating5?: number;            // 0–5
  reviewsCount?: number;
  distanceKmFromAirport?: number | null;
  nights: number;
  travellers: number;
  pricePerNight: number;
  taxesAndFees?: number;       // optional
  imageUrl?: string | null;
  bullets?: string[];
  overall10?: number;          // “Overall 8.4”
  onPress?: () => void;
};

export default function HotelResultCard({
  name, stars = 0, rating5, reviewsCount, distanceKmFromAirport,
  nights, travellers, pricePerNight, taxesAndFees, imageUrl,
  bullets = [], overall10, onPress
}: Props) {
  const total = nights * pricePerNight;

  // ----- resilient image handling -----
  const primaryFallback = useMemo(
    () => "https://picsum.photos/seed/hotel-fallback-1/520/360",
    []
  );
  const secondaryFallback = useMemo(
    () => "https://picsum.photos/seed/hotel-fallback-2/520/360",
    []
  );
  const [imgUri, setImgUri] = useState<string>(imageUrl || primaryFallback);

  return (
    <View style={{
      borderRadius: 12, borderWidth: 1, borderColor: "#e5e7eb",
      backgroundColor: "#fff", overflow: "hidden", marginBottom: 14
    }}>
      <View style={{ flexDirection: "row" }}>
        <Image
          key={imgUri} // force rerender when uri changes
          source={{ uri: imgUri }}
          onError={() => {
            // try secondary fallback if primary/real fails
            setImgUri((prev) => (prev === primaryFallback ? secondaryFallback : secondaryFallback));
          }}
          resizeMode="cover"
          style={{
            width: 150,
            height: 150,
            backgroundColor: "#eee"
          }}
          accessibilityLabel={`${name} photo`}
        />

        <View style={{ flex: 1, padding: 12 }}>
          <Text style={{ fontSize: 18, fontWeight: "800" }} numberOfLines={2}>{name}</Text>

          <View style={{ flexDirection: "row", alignItems: "center", marginTop: 6, gap: 8 }}>
            <Text style={{ color: "#f59e0b" }}>
              {Array.from({ length: stars }).map((_, i) => "★").join("")}
              <Text style={{ color: "#d1d5db" }}>
                {Array.from({ length: Math.max(0, 5 - stars) }).map(() => "☆").join("")}
              </Text>
            </Text>

            {distanceKmFromAirport != null && (
              <Text style={{ color: "#6b7280" }}>
                {distanceKmFromAirport} km from YYZ
              </Text>
            )}
          </View>

          <View style={{ flexDirection: "row", alignItems: "center", marginTop: 6, gap: 8 }}>
            {overall10 != null && (
              <View style={{ backgroundColor: "#1e40af", borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 }}>
                <Text style={{ color: "#fff", fontWeight: "800" }}>{overall10.toFixed(1)}</Text>
              </View>
            )}
            {reviewsCount != null && rating5 != null && (
              <Text style={{ color: "#374151" }}>
                {rating5.toFixed(1)}/5 · {reviewsCount} reviews
              </Text>
            )}
          </View>

          {bullets.slice(0, 3).map((b, i) => (
            <Text key={i} style={{ color: "#059669", marginTop: 4 }}>✓ {b}</Text>
          ))}
        </View>
      </View>

      <View style={{
        padding: 12, borderTopWidth: 1, borderTopColor: "#f3f4f6",
        flexDirection: "row", justifyContent: "space-between", alignItems: "center"
      }}>
        <Text style={{ color: "#6b7280" }}>
          {nights} {nights === 1 ? "night" : "nights"}, {travellers} {travellers === 1 ? "adult" : "adults"}
        </Text>
        <View style={{ alignItems: "flex-end" }}>
          <Text style={{ fontSize: 20, fontWeight: "800" }}>CAD {total.toLocaleString("en-CA")}</Text>
          <Text style={{ color: "#6b7280", fontSize: 12 }}>
            +CAD {(taxesAndFees ?? Math.round(total * 0.13)).toLocaleString("en-CA")} taxes and charges
          </Text>
          <Pressable onPress={onPress} style={{
            marginTop: 8, backgroundColor: "#2F6BFF", borderRadius: 8,
            paddingHorizontal: 14, paddingVertical: 10
          }}>
            <Text style={{ color: "#fff", fontWeight: "700" }}>View property</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}
