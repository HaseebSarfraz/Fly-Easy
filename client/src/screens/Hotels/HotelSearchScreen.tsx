import React, { useMemo, useState } from "react";
import { Text, StyleSheet, View, Pressable, TextInput, Modal } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { Calendar } from "react-native-calendars";

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
  const [checkInDate, setCheckInDate] = useState("");
  const [checkOutDate, setCheckOutDate] = useState("");
  const [showCalendar, setShowCalendar] = useState<"checkin" | "checkout" | null>(null);

  const today = new Date().toISOString().split("T")[0];

  const canContinue = useMemo(() => {
    const t = Number(travellers);
    return city.trim().length > 0 && !Number.isNaN(t) && t > 0 && checkInDate && checkOutDate;
  }, [city, travellers, checkInDate, checkOutDate]);

  const onContinue = () => {
    const t = Number(travellers);
    navigation.navigate("HotelPreferences", {
      location: city.trim(),
      travellers: Number.isNaN(t) ? 1 : t,
      checkIn: checkInDate,
      checkOut: checkOutDate,
    });
  };

  const handleDateSelect = (dateString: string) => {
    if (showCalendar === "checkin") {
      setCheckInDate(dateString);
      if (checkOutDate && dateString > checkOutDate) {
        setCheckOutDate("");
      }
    } else if (showCalendar === "checkout") {
      setCheckOutDate(dateString);
    }
    setShowCalendar(null);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.header}>Book Your Stay</Text>

        <Text style={styles.label}>Location*</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. Mississauga"
          value={city}
          onChangeText={setCity}
          autoCapitalize="words"
          returnKeyType="next"
        />

        <Text style={styles.label}>Travellers*</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. 2"
          value={travellers}
          onChangeText={setTravellers}
          keyboardType="number-pad"
          returnKeyType="next"
        />

        <View style={styles.row}>
          <View style={styles.field}>
            <Text style={styles.label}>Check-in*</Text>
            <Pressable style={styles.dateButton} onPress={() => setShowCalendar("checkin")}>
              <Text style={[styles.dateText, !checkInDate && styles.placeholder]}>
                {checkInDate || "Select Date..."}
              </Text>
            </Pressable>
          </View>

          <View style={[styles.field, { marginLeft: 12 }]}>
            <Text style={styles.label}>Check-out*</Text>
            <Pressable style={styles.dateButton} onPress={() => setShowCalendar("checkout")}>
              <Text style={[styles.dateText, !checkOutDate && styles.placeholder]}>
                {checkOutDate || "Select Date..."}
              </Text>
            </Pressable>
          </View>
        </View>

        <Pressable style={[styles.button, !canContinue && { opacity: 0.6 }]} onPress={onContinue} disabled={!canContinue}>
          <Text style={styles.buttonText}>Continue</Text>
        </Pressable>
      </View>

      <Modal visible={showCalendar !== null} transparent animationType="fade">
        <Pressable style={styles.modalOverlay} onPress={() => setShowCalendar(null)}>
          <View style={styles.calendarContainer}>
            <Calendar
              minDate={showCalendar === "checkin" ? today : checkInDate || today}
              onDayPress={(day) => handleDateSelect(day.dateString)}
              markedDates={{
                [checkInDate]: { selected: true, selectedColor: "#2F6BFF" },
                [checkOutDate]: { selected: true, selectedColor: "#2F6BFF" },
              }}
              theme={{
                selectedDayBackgroundColor: "#2F6BFF",
                todayTextColor: "#2F6BFF",
                arrowColor: "#2F6BFF",
              }}
            />
            <Pressable style={styles.closeButton} onPress={() => setShowCalendar(null)}>
              <Text style={styles.closeButtonText}>Close</Text>
            </Pressable>
          </View>
        </Pressable>
      </Modal>
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
  dateButton: {
    height: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#CFCFD6",
    paddingHorizontal: 12,
    backgroundColor: "#fff",
    justifyContent: "center",
    marginBottom: 14,
  },
  dateText: {
    fontSize: 16,
    color: "#000",
  },
  placeholder: {
    color: "#999",
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
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "center",
    alignItems: "center",
  },
  calendarContainer: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    width: "90%",
  },
  closeButton: {
    marginTop: 12,
    height: 48,
    borderRadius: 12,
    backgroundColor: "#2F6BFF",
    alignItems: "center",
    justifyContent: "center",
  },
  closeButtonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
  },
});