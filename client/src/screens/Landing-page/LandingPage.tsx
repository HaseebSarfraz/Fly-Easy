import React from "react";
import { Text, StyleSheet, View, Pressable, Image } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

// @ts-ignore
export default function LandingPageScreen({ navigation }) {
    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.container}>
                <Image
                    source={require("../../../assets/airplane-take-off.png")}
                    style={styles.logo}
                />

                <Text style={styles.title}>Welcome to Fly Easy</Text>
                <Text style={styles.subtitle}>Your travel made simple.</Text>

                <View style={styles.buttonContainer}>
                    <Pressable
                        style={[styles.button, styles.primaryButton]}
                        onPress={() => navigation.navigate("HotelSearch")}
                    >
                        <Text style={styles.buttonText}>Search Hotels</Text>
                    </Pressable>

                    <Pressable
                        style={[styles.button, styles.secondaryButton]}
                        onPress={() => navigation.navigate("RestaurantsSearch")}
                    >
                        <Text style={[styles.buttonText, styles.secondaryText]}>
                           Search Restaurants
                        </Text>
                    </Pressable>

                    <Pressable
                        style={[styles.button, styles.walletButton]}
                        onPress={() => navigation.navigate("DigitalWallet")}
                    >
                        <Text style={styles.buttonText}>💳 Digital Wallet</Text>
                    </Pressable>
                </View>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safe: {
        flex: 1,
        backgroundColor: "#ffffff",
    },
    container: {
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
        padding: 24,
    },
    logo: {
        width: 100,
        height: 100,
        marginBottom: 24,
    },
    title: {
        fontSize: 32,
        fontWeight: "700",
        marginBottom: 8,
        color: "#2F6BFF",
        textAlign: "center",
    },
    subtitle: {
        fontSize: 16,
        fontWeight: "500",
        color: "#555",
        textAlign: "center",
        marginBottom: 40,
    },
    buttonContainer: {
        width: "100%",
        gap: 16,
    },
    button: {
        height: 50,
        borderRadius: 12,
        justifyContent: "center",
        alignItems: "center",
    },
    primaryButton: {
        backgroundColor: "#2F6BFF",
    },
    secondaryButton: {
        borderWidth: 1.5,
        borderColor: "#2F6BFF",
    },
    walletButton: {
        backgroundColor: "#4CAF50",
    },
    buttonText: {
        fontSize: 16,
        fontWeight: "600",
        color: "#fff",
    },
    secondaryText: {
        color: "#2F6BFF",
    },
});
