import React from "react";
import { Text, StyleSheet, View, Pressable, Image, Animated, Dimensions } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from "@react-navigation/native-stack";

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');


interface FlyingPlaneProps {
  delay: number;
  speed: number;
  yPosition: number;
  icon: keyof typeof Ionicons.glyphMap;
}

const FlyingPlane = ({ delay, speed, yPosition, icon }: FlyingPlaneProps) => {
  const translateX = React.useRef(new Animated.Value(-100)).current;

  React.useEffect(() => {
    const animate = () => {
      translateX.setValue(-100);
      Animated.timing(translateX, {
        toValue: SCREEN_WIDTH + 100,
        duration: speed,
        useNativeDriver: true,
        delay,
      }).start(() => animate());
    };
    animate();
  }, []);

  return (
    <Animated.View
      style={{
        position: 'absolute',
        transform: [{ translateX }],
        top: yPosition,
      }}
    >
      <Ionicons name={icon} size={23} color="#0339ff82" style={{ opacity: 0.5 }} />
    </Animated.View>
  );
};

type LandingPageScreenProps = NativeStackScreenProps<any, 'LandingPage'>;

export default function LandingPageScreen({ navigation }: LandingPageScreenProps) {
    const planes = React.useMemo(() => {
        return Array.from({ length: 100 }).map((_, i) => ({
            key: i,
            delay: Math.random() * 10000,
            speed: 6000 + Math.random() * 12000,
            yPosition: Math.random() * SCREEN_HEIGHT,
            icon: (Math.random() > 0.5 ? "airplane-outline" : "airplane-sharp") as keyof typeof Ionicons.glyphMap
        }));
    }, []);

    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.container}>
                <View style={StyleSheet.absoluteFill} pointerEvents="none">
                    {planes.map(plane => (
                        <FlyingPlane
                            key={plane.key}
                            delay={plane.delay}
                            speed={plane.speed}
                            yPosition={plane.yPosition}
                            icon={plane.icon}
                        />
                    ))}
                </View>

                <Text style={styles.title}>Welcome to Fly Easy</Text>
                <Text style={styles.subtitle}>Your travel made simple.</Text>

                <View style={styles.buttonContainer}>
                    <Pressable
                        style={[styles.button, styles.primaryButton]}
                        onPress={() => navigation.navigate("HotelSearch")}
                    >
                        <Text style={styles.buttonText}>🏨 Search Hotels</Text>
                    </Pressable>

                    <Pressable
                        style={[styles.button, styles.secondaryButton]}
                        onPress={() => navigation.navigate("RestaurantsSearch")}
                    >
                        <Text style={[styles.buttonText, styles.secondaryText]}>
                           🍽️ Search Restaurants
                        </Text>
                    </Pressable>

                    <Pressable
                        style={[styles.button, styles.walletButton]}
                        onPress={() => navigation.navigate("DigitalWallet")}
                    >
                        <Text style={styles.buttonText}>💳 Digital Wallet</Text>
                    </Pressable>

                    <Pressable
                        style={[styles.button, styles.secondaryButton]}
                        onPress={() => navigation.navigate("AirportTracker")}
                    >
                        <Text style={[styles.buttonText, styles.secondaryText]}>📃 All Flights</Text>
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
        zIndex: 1,
    },
    title: {
        fontSize: 32,
        fontWeight: "700",
        marginBottom: 8,
        color: "#2F6BFF",
        textAlign: "center",
        zIndex: 1,
    },
    subtitle: {
        fontSize: 16,
        fontWeight: "500",
        color: "#555",
        textAlign: "center",
        marginBottom: 40,
        zIndex: 1,
    },
    buttonContainer: {
        width: "100%",
        gap: 16,
        zIndex: 1,
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
    }
});