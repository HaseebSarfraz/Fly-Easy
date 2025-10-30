// src/screens/Hotels/HotelSearchScreen.tsx
import React, { useMemo, useState } from "react";
import { Text, StyleSheet, View, TextInput, Pressable } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { NativeStackScreenProps } from "@react-navigation/native-stack";

type RootStackParamList = {
  LandingPage: undefined;
  HotelSearch: undefined;
  HotelPreferences: { location: string; travellers: number; checkIn: string; checkOut: string };
  RestaurantsSearch: undefined;
};

type Props = NativeStackScreenProps<RootStackParamList, "HotelSearch">;

export default function HotelSearchScreen({ navigation }: Props) {
  const [city, setCity] = useState("");
  const [travellers, setTravellers] = useState("1");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");

  const canContinue = useMemo(() => {
    const t = Number(travellers);
    return city.trim().length > 0 && !Number.isNaN(t) && t > 0 && checkIn.trim() && checkOut.trim();
  }, [city, travellers, checkIn, checkOut]);

  const onContinue = () => {
    const t = Number(travellers);
    navigation.navigate("HotelPreferences", {
      location: city.trim(),
      travellers: Number.isNaN(t) ? 1 : t,
      checkIn: checkIn.trim(),
      checkOut: checkOut.trim(),
    });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.header}>Book Your Stay</Text>

        <Text style={styles.label}>Location</Text>
        <TextInput
          style={[styles.input]}
          placeholder="e.g. Mississauga"
          value={city}
          onChangeText={setCity}
          autoCapitalize="words"
          returnKeyType="next"
        />

        <Text style={styles.label}>Travellers</Text>
        <TextInput
          style={[styles.input]}
          placeholder="e.g. 2"
          value={travellers}
          onChangeText={setTravellers}
          keyboardType="number-pad"
          returnKeyType="next"
        />

        <View style={styles.row}>
          <View style={styles.field}>
            <Text style={styles.label}>Check-in</Text>
            <TextInput
              style={styles.input2}
              placeholder="YYYY-MM-DD"
              value={checkIn}
              onChangeText={setCheckIn}
              autoCapitalize="none"
            />
          </View>

          <View style={[styles.field, { marginLeft: 12 }]}>
            <Text style={styles.label}>Check-out</Text>
            <TextInput
              style={styles.input2}
              placeholder="YYYY-MM-DD"
              value={checkOut}
              onChangeText={setCheckOut}
              autoCapitalize="none"
            />
          </View>
        </View>

        <Pressable style={[styles.button, !canContinue && { opacity: 0.6 }]} onPress={onContinue} disabled={!canContinue}>
          <Text style={styles.buttonText}>Continue</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#fff" },
  container: { padding: 16 },
  header: { fontSize: 28, fontWeight: "700", marginBottom: 12 },
  label: { fontSize: 14, fontWeight: "600", marginBottom: 6 },
  input: {
    height: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#CFCFD6",
    paddingHorizontal: 12,
    backgroundColor: "#fff",
    marginBottom: 14,
  },
  input2: {
    height: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#CFCFD6",
    paddingHorizontal: 12,
    marginBottom: 14,
  },
  row: { flexDirection: "row", alignItems: "flex-start" },
  field: { flex: 1, minWidth: 0 },
  button: {
    marginTop: 12,
    height: 48,
    borderRadius: 12,
    backgroundColor: "#2F6BFF",
    alignItems: "center",
    justifyContent: "center",
  },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 16 },
});
