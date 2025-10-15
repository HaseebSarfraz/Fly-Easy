import React, { useMemo, useState } from "react";
import { SafeAreaView, View, Text, TextInput, Pressable, StyleSheet } from "react-native";
import { NativeStackScreenProps } from "@react-navigation/native-stack";

type RootStackParamList = {
  HotelSearch: undefined;
  HotelPreferences: { location: string; travellers: number; checkIn: string; checkOut: string };
  HotelsScreen: any;
};

type Props = NativeStackScreenProps<RootStackParamList, "HotelPreferences">;

function Chip({
  label,
  selected,
  onPress,
}: { label: string; selected?: boolean; onPress?: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.chip, selected ? styles.chipSelected : styles.chipUnselected]}>
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{label}</Text>
    </Pressable>
  );
}

export default function HotelPreferencesScreen({ route, navigation }: Props) {
  // SAFE read (no crash if dev navigates without params)
  const { location = "", travellers = 1, checkIn = "", checkOut = "" } = route?.params ?? {};

  // ---- Budget (min/max) ----
  const [minBudget, setMinBudget] = useState<string>("");
  const [maxBudget, setMaxBudget] = useState<string>("");

  // ---- Rating: 1★–5★ ----
  const [rating, setRating] = useState<number>(4); // default 4+

  // ---- Cancellation options ----
  type CancelOpt = "24h" | "48h" | "Free" | "Any";
  const [cancelOpt, setCancelOpt] = useState<CancelOpt>("Free");

  // ---- Payment options ----
  type PaymentOpt = "Online" | "In-person";
  const [payOpt, setPayOpt] = useState<PaymentOpt>("Online");

  const canSeeResults = useMemo(() => true, []);

  const onSeeResults = () => {
    navigation.navigate("HotelsScreen", {
      // base
      location,
      travellers,
      checkIn,
      checkOut,
      // preferences to feed the AI
      budgetPerNightRange: [
        minBudget.trim() ? Number(minBudget) : undefined,
        maxBudget.trim() ? Number(maxBudget) : undefined,
      ],
      minRating: rating, // 1..5
      cancellationPreference: cancelOpt, // "24h" | "48h" | "Free" | "Any"
      paymentPreference: payOpt, // "Online" | "In-person"
    });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.content}>
        <Text style={styles.title}>Tailor Your Stay</Text>

        {/* Budget range */}
        <Text style={styles.sectionTitle}>Budget per night (CAD)</Text>
        <View style={styles.row}>
          <View style={[styles.field, { marginRight: 8 }]}>
            <Text style={styles.label}>Min</Text>
            <TextInput
              style={styles.input}
              placeholder="$ e.g. 120"
              keyboardType="number-pad"
              value={minBudget}
              onChangeText={setMinBudget}
            />
          </View>
          <View style={styles.field}>
            <Text style={styles.label}>Max</Text>
            <TextInput
              style={styles.input}
              placeholder="$ e.g. 240"
              keyboardType="number-pad"
              value={maxBudget}
              onChangeText={setMaxBudget}
            />
          </View>
        </View>

        {/* Rating 1★–5★ */}
        <Text style={[styles.sectionTitle, { marginTop: 16 }]}>Minimum rating</Text>
        <View style={styles.rowWrap}>
          {[1, 2, 3, 4, 5].map((r) => (
            <Chip key={r} label={`${r}★+`} selected={rating === r} onPress={() => setRating(r)} />
          ))}
        </View>

        {/* Cancellation options */}
        <Text style={[styles.sectionTitle, { marginTop: 16 }]}>Cancellation</Text>
        <View style={styles.rowWrap}>
          {(["24h", "48h", "Free", "Any"] as CancelOpt[]).map((c) => (
            <Chip
              key={c}
              label={c === "Free" ? "Free until check-in" : c === "Any" ? "Any policy" : `${c} from booking`}
              selected={cancelOpt === c}
              onPress={() => setCancelOpt(c)}
            />
          ))}
        </View>

        {/* Payment options */}
        <Text style={[styles.sectionTitle, { marginTop: 16 }]}>Preferred Payment Method</Text>
        <View style={styles.rowWrap}>
          {(["Online", "In-person", "Any"] as PaymentOpt[]).map((p) => (
            <Chip key={p} label={p} selected={payOpt === p} onPress={() => setPayOpt(p)} />
          ))}
        </View>

        <Pressable style={[styles.primaryBtn, !canSeeResults && styles.btnDisabled]} onPress={onSeeResults} disabled={!canSeeResults}>
          <Text style={styles.primaryBtnText}>See results</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#fff" },
  content: { padding: 16, paddingBottom: 32 },
  title: { fontSize: 26, fontWeight: "700", marginBottom: 12 },
  sectionTitle: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
  label: { fontSize: 13, color: "#6b7280", marginBottom: 6 },

  row: { flexDirection: "row" },
  field: { flex: 1, minWidth: 0 },

  rowWrap: { flexDirection: "row", flexWrap: "wrap", gap: 8 },

  input: {
    height: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#CFCFD6",
    paddingHorizontal: 12,
    backgroundColor: "#fff",
    marginBottom: 12,
  },

  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    marginBottom: 8,
  },
  chipSelected: { backgroundColor: "#3B82F6", borderColor: "#3B82F6" },
  chipUnselected: { backgroundColor: "#fff", borderColor: "#CFCFD6" },
  chipText: { fontSize: 14, fontWeight: "600", color: "#111827" },
  chipTextSelected: { color: "#fff" },

  primaryBtn: {
    marginTop: 22,
    backgroundColor: "#3B82F6",
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },
  primaryBtnText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  btnDisabled: { opacity: 0.6 },
});