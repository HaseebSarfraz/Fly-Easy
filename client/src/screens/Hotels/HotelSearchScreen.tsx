import React from "react";
import { SafeAreaView, Text, StyleSheet, View, TextInput} from "react-native";
import {useState} from "react";
import {Pressable} from "react-native";
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

    const onContinue = () => {
        navigation.navigate("HotelPreferences", {
        location: city.trim(),
        travellers: Number(travellers),
        checkIn,
        checkOut,
        });
    };

    return (
        
        <SafeAreaView style={styles.safe}>

            <View style={styles.container}>

                <Text style={styles.header}>Book Your Stay</Text>

                <Text style={styles.label}>Location</Text>
                <TextInput style={[styles.label, styles.input]} placeholder="Location"/>

                <Text style={styles.label}>Travellers</Text>
                <TextInput style={[styles.label, styles.input]} placeholder="5"/>

            
            <View style={styles.row}>

                <View style={styles.field}>
                
                    <Text style={styles.label}>Check-in</Text>
                    <TextInput style={[styles.input2]}
                    placeholder="YYYY-MM-DD"
                    />

                </View>

                <View style={styles.field}>

                    <Text style={styles.label}>Check-out</Text>
                    <TextInput style={[styles.input2]}
                    placeholder="YYYY-MM-DD"
                    />

                </View>
                   
            </View>

            <Pressable style={styles.button}
             onPress={onContinue}>

                <Text style={styles.buttonText}>Continue</Text>

            </Pressable>

          </View>
        </SafeAreaView>
    );

}

const styles = StyleSheet.create({

    safe: {flex: 1, backgroundColor: "#ffffffff"},
    container: {padding: 16}, 
    header: { fontSize: 28, fontWeight: "700", marginBottom: 12},
    label: {fontSize: 14, fontWeight: "600", marginBottom: 6},
    input: {

        height: 48,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: "#090303ff",
        paddingHorizontal: 12,
        backgroundColor: "#fff",
        marginBottom: 14,
    },

    input2: {

        height: 48,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: "#090303ff",
        paddingHorizontal: 12,
        marginBottom: 14,
        width: 150,
    },
    row: {
        flexDirection: 'row',
        alignItems: 'flex-start',
    },
    field: {
        flex: 1,
        minWidth: 0,
    },

    button: {
    marginTop: 12,
    height: 48,
    borderRadius: 12,
    backgroundColor: "#2F6BFF",
    alignItems: "center",
    justifyContent: "center",
    },

    buttonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
    },

});