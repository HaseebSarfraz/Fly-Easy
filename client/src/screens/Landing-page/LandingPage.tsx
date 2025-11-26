import React, { useState, useEffect } from "react";
import { Text, StyleSheet, View, Pressable, Animated, Dimensions, TextInput } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import AsyncStorage from '@react-native-async-storage/async-storage';

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
    setTimeout(() => {
      const animate = () => {
        translateX.setValue(-100);
        Animated.timing(translateX, {
          toValue: SCREEN_WIDTH + 100,
          duration: speed,
          useNativeDriver: true,
          delay: 0,
        }).start(() => animate());
      };
      animate();
    }, delay);
  }, []);

  return (
    <Animated.View style={{ position: 'absolute', transform: [{ translateX }], top: yPosition }}>
      <Ionicons name={icon} size={23} color="#0339ff82" style={{ opacity: 0.5 }} />
    </Animated.View>
  );
};

type LandingPageScreenProps = NativeStackScreenProps<any, 'LandingPage'>;

export default function LandingPageScreen({ navigation }: LandingPageScreenProps) {
    const [flightNumber, setFlightNumber] = useState('');
    const [trackedFlight, setTrackedFlight] = useState<string | null>(null);
    const [flightData, setFlightData] = useState<any>(null);
    const [countdown, setCountdown] = useState('');

    const planes = React.useMemo(() => {
        return Array.from({ length: 100 }).map((_, i) => ({
            key: i,
            delay: Math.random() * 5000,
            speed: 6000 + Math.random() * 12000,
            yPosition: Math.random() * SCREEN_HEIGHT,
            icon: (Math.random() > 0.5 ? "airplane-outline" : "airplane-sharp") as keyof typeof Ionicons.glyphMap
        }));
    }, []);

    useEffect(() => {
      const loadFlight = async () => {
        const saved = await AsyncStorage.getItem('trackedFlight');
        if (saved) {
          setTrackedFlight(saved);
          fetchFlightData(saved);
        }
      };
      loadFlight();
    }, []);

    const fetchFlightData = async (flight: string) => {
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(
        `https://aerodatabox.p.rapidapi.com/flights/number/${flight}/${today}`,
        {
            headers: {
            'X-RapidAPI-Key': 'a75d212df3msh80b4775bd20989bp1ac458jsn28c53dce7038',
            'X-RapidAPI-Host': 'aerodatabox.p.rapidapi.com'
            }
        }
        );
        
        const data = await response.json();
        console.log('Flight data:', data);
        
        if (data && data.length > 0) {
        setFlightData(data[0]);
        }
    } catch (error) {
        console.error('Error:', error);
    }
    };

    const handleTrackFlight = async () => {
      await AsyncStorage.setItem('trackedFlight', flightNumber);
      setTrackedFlight(flightNumber);
      fetchFlightData(flightNumber);
    };

    useEffect(() => {
    if (!flightData?.departure?.scheduledTime?.local) return;

    const interval = setInterval(() => {
        const now = new Date().getTime();
        // Parse the local time string properly
        const departureTime = new Date(flightData.departure.scheduledTime.local).getTime();
        const diff = departureTime - now;

        if (diff < 0) {
        setCountdown('Departed');
        clearInterval(interval)
        return;
        }

        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);

        setCountdown(`${hours}h ${minutes}m ${seconds}s`);
    }, 1000);

    return () => clearInterval(interval);
    }, [flightData]);

    return (
        <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
            <View style={styles.container}>
                <View style={styles.animationContainer}>
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

                {!trackedFlight ? (
                  <View style={styles.flightInput}>
                    <TextInput
                      style={styles.input}
                      placeholder="Enter flight number"
                      value={flightNumber}
                      onChangeText={setFlightNumber}
                      autoCapitalize="characters"
                      placeholderTextColor="#999"
                    />
                    <Pressable style={styles.trackButton} onPress={handleTrackFlight}>
                      <Text style={styles.trackButtonText}>Track</Text>
                    </Pressable>
                  </View>
                ) : (
                  <View style={styles.countdownBox}>
                    <Text style={styles.flightNum}>{trackedFlight}</Text>
                    <Text style={styles.countdownText}>{countdown}</Text>
                    <Pressable onPress={async () => { 
                      setTrackedFlight(null); 
                      await AsyncStorage.removeItem('trackedFlight'); 
                    }}>
                      <Text style={styles.changeText}>Change Flight</Text>
                    </Pressable>
                  </View>
                )}

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
        marginBottom: 24,
        zIndex: 1,
    },
    flightInput: {
        flexDirection: 'row',
        width: '100%',
        marginBottom: 24,
        gap: 8,
        zIndex: 1,
    },
    input: {
        flex: 1,
        height: 48,
        borderWidth: 1,
        borderColor: '#CFCFD6',
        borderRadius: 12,
        paddingHorizontal: 12,
        backgroundColor: '#fff',
    },
    trackButton: {
        height: 48,
        backgroundColor: '#2F6BFF',
        borderRadius: 12,
        paddingHorizontal: 24,
        justifyContent: 'center',
    },
    trackButtonText: {
        color: '#fff',
        fontWeight: '600',
        fontSize: 16,
    },
    countdownBox: {
        padding: 20,
        backgroundColor: '#f5f5f5',
        borderRadius: 12,
        marginBottom: 24,
        alignItems: 'center',
        width: '100%',
        zIndex: 1,
    },
    flightNum: {
        fontSize: 24,
        fontWeight: '700',
        color: '#2F6BFF',
    },
    countdownText: {
        fontSize: 36,
        fontWeight: '700',
        marginTop: 8,
        color: '#333',
    },
    changeText: {
        color: '#2F6BFF',
        marginTop: 8,
        textDecorationLine: 'underline',
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
        backgroundColor: "#fff"
    },
    walletButton: {
        backgroundColor: "#2F6BFF",
    },
    buttonText: {
        fontSize: 16,
        fontWeight: "600",
        color: "#fff",
    },
    secondaryText: {
        color: "#2F6BFF",
    },
    animationContainer: {
        ...StyleSheet.absoluteFillObject,
        overflow: 'visible',
        pointerEvents: 'none',
    },
});