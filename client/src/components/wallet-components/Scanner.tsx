import React, { useState, useRef } from "react";
import {
    Text,
    StyleSheet,
    View,
    Pressable,
    Image,
    Alert,
    TextInput,
    ScrollView,
    KeyboardAvoidingView,
    Platform,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import * as ImageManipulator from "expo-image-manipulator";
import * as FileSystem from "expo-file-system/legacy";

// @ts-ignore
export default function BoardingPassScannerScreen({ navigation, route }) {
    const [permission, requestPermission] = useCameraPermissions();
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [isCameraActive, setIsCameraActive] = useState(false);
    const cameraRef = useRef<any>(null);

    // Boarding pass details
    const [passengerName, setPassengerName] = useState("");
    const [flightNumber, setFlightNumber] = useState("");
    const [seatNumber, setSeatNumber] = useState("");
    const [gateNumber, setGateNumber] = useState("");

    const onSave = route.params?.onSave;

    if (!permission) {
        return <View />;
    }

    if (!permission.granted) {
        return (
            <SafeAreaView style={styles.safe}>
                <View style={styles.container}>
                    <Text style={styles.title}>Camera Permission Required</Text>
                    <Text style={styles.subtitle}>
                        We need camera access to scan boarding passes
                    </Text>
                    <Pressable style={styles.primaryButton} onPress={requestPermission}>
                        <Text style={styles.buttonText}>Grant Permission</Text>
                    </Pressable>
                </View>
            </SafeAreaView>
        );
    }

    const takePicture = async () => {
        if (cameraRef.current) {
            try {
                const photo = await cameraRef.current.takePictureAsync({
                    quality: 0.8,
                });
                setCapturedImage(photo.uri);
                setIsCameraActive(false);
            } catch (error) {
                console.error("Error taking picture:", error);
                Alert.alert("Error", "Failed to take picture");
            }
        }
    };

    const pickImage = async () => {
        const result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ["images"],
            allowsEditing: false,
            quality: 1,
        });

        if (!result.canceled && result.assets[0]) {
            setCapturedImage(result.assets[0].uri);
        }
    };

    const rotateImage = async () => {
        if (!capturedImage) return;

        try {
            const manipResult = await ImageManipulator.manipulateAsync(
                capturedImage,
                [{ rotate: 90 }],
                { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG }
            );
            setCapturedImage(manipResult.uri);
        } catch (error) {
            console.error("Error rotating:", error);
            Alert.alert("Error", "Failed to rotate image");
        }
    };

    const saveBoardingPass = async () => {
        if (!capturedImage) return;

        // Validate required fields
        if (!passengerName.trim()) {
            Alert.alert("Missing Info", "Please enter passenger name");
            return;
        }
        if (!flightNumber.trim()) {
            Alert.alert("Missing Info", "Please enter flight number");
            return;
        }

        try {
            const walletDir = (FileSystem as any).documentDirectory + "wallet/";
            
            console.log("Wallet directory:", walletDir);
            
            const dirInfo = await FileSystem.getInfoAsync(walletDir);

            if (!dirInfo.exists) {
                await FileSystem.makeDirectoryAsync(walletDir, { intermediates: true });
                console.log("Created wallet directory");
            }

            const id = Date.now().toString();
            const imageUri = walletDir + id + ".jpg";
            const metadataUri = walletDir + id + ".json";

            console.log("Saving to:", imageUri);

            // Copy image
            await FileSystem.copyAsync({
                from: capturedImage,
                to: imageUri,
            });

            console.log("Image copied successfully");

            // Save metadata with boarding pass details
            const metadata = {
                id,
                imageUri: imageUri,
                passengerName: passengerName.trim(),
                flightNumber: flightNumber.trim(),
                seatNumber: seatNumber.trim(),
                gateNumber: gateNumber.trim(),
                timestamp: new Date().toISOString(),
            };

            await FileSystem.writeAsStringAsync(metadataUri, JSON.stringify(metadata));
            
            console.log("Metadata saved:", metadata);

            Alert.alert("Success", "Boarding pass saved!", [
                {
                    text: "OK",
                    onPress: () => {
                        if (onSave) onSave();
                        navigation.goBack();
                    },
                },
            ]);
        } catch (error) {
            console.error("Error saving:", error);
            Alert.alert("Error", `Failed to save boarding pass: ${error}`);
        }
    };

    if (isCameraActive) {
        return (
            <View style={{ flex: 1 }}>
                <CameraView style={styles.camera} ref={cameraRef} />
                <View style={styles.cameraOverlay}>
                    <View style={styles.cameraHeader}>
                        <Pressable
                            style={styles.closeButton}
                            onPress={() => setIsCameraActive(false)}
                        >
                            <Text style={styles.closeText}>×</Text>
                        </Pressable>
                    </View>

                    <View style={styles.cameraFooter}>
                        <Pressable style={styles.captureButton} onPress={takePicture}>
                            <View style={styles.captureButtonInner} />
                        </Pressable>
                    </View>
                </View>
            </View>
        );
    }

    if (capturedImage) {
        return (
            <SafeAreaView style={styles.safe} edges={['top']}>
                <KeyboardAvoidingView 
                    behavior={Platform.OS === "ios" ? "padding" : "height"}
                    style={styles.keyboardView}
                >
                    <ScrollView 
                        contentContainerStyle={styles.scrollContent}
                        keyboardShouldPersistTaps="handled"
                    >
                        <Text style={styles.title}>Boarding Pass Details</Text>

                        <Image 
                            source={{ uri: capturedImage }} 
                            style={styles.previewImage}
                            resizeMode="contain"
                        />

                        <Pressable style={styles.rotateButton} onPress={rotateImage}>
                            <Text style={styles.rotateButtonText}>🔄 Rotate</Text>
                        </Pressable>

                        <View style={styles.formContainer}>
                            <Text style={styles.label}>Passenger Name *</Text>
                            <TextInput
                                style={styles.input}
                                value={passengerName}
                                onChangeText={setPassengerName}
                                placeholder="e.g., John Smith"
                                placeholderTextColor="#999"
                            />

                            <Text style={styles.label}>Flight Number *</Text>
                            <TextInput
                                style={styles.input}
                                value={flightNumber}
                                onChangeText={setFlightNumber}
                                placeholder="e.g., AA1234"
                                placeholderTextColor="#999"
                                autoCapitalize="characters"
                            />

                            <Text style={styles.label}>Seat Number</Text>
                            <TextInput
                                style={styles.input}
                                value={seatNumber}
                                onChangeText={setSeatNumber}
                                placeholder="e.g., 12A"
                                placeholderTextColor="#999"
                                autoCapitalize="characters"
                            />

                            <Text style={styles.label}>Gate Number</Text>
                            <TextInput
                                style={styles.input}
                                value={gateNumber}
                                onChangeText={setGateNumber}
                                placeholder="e.g., B5"
                                placeholderTextColor="#999"
                                autoCapitalize="characters"
                            />
                        </View>

                        <View style={styles.actionButtons}>
                            <Pressable
                                style={[styles.button, styles.secondaryButton]}
                                onPress={() => {
                                    setCapturedImage(null);
                                    setPassengerName("");
                                    setFlightNumber("");
                                    setSeatNumber("");
                                    setGateNumber("");
                                }}
                            >
                                <Text style={[styles.buttonText, styles.secondaryText]}>
                                    Cancel
                                </Text>
                            </Pressable>
                            <Pressable
                                style={[styles.button, styles.primaryButton]}
                                onPress={saveBoardingPass}
                            >
                                <Text style={styles.buttonText}>Save</Text>
                            </Pressable>
                        </View>
                    </ScrollView>
                </KeyboardAvoidingView>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.container}>
                <Text style={styles.title}>Scan Boarding Pass</Text>
                <Text style={styles.subtitle}>Take a photo or select from gallery</Text>

                <View style={styles.optionButtons}>
                    <Pressable
                        style={[styles.button, styles.primaryButton]}
                        onPress={() => setIsCameraActive(true)}
                    >
                        <Text style={styles.buttonText}>📷 Take Photo</Text>
                    </Pressable>

                    <Pressable
                        style={[styles.button, styles.secondaryButton]}
                        onPress={pickImage}
                    >
                        <Text style={[styles.buttonText, styles.secondaryText]}>
                            📁 Choose from Gallery
                        </Text>
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
    keyboardView: {
        flex: 1,
    },
    scrollContent: {
        padding: 24,
        paddingBottom: 40,
    },
    container: {
        flex: 1,
        padding: 24,
        justifyContent: "center",
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
    optionButtons: {
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
    buttonText: {
        fontSize: 16,
        fontWeight: "600",
        color: "#fff",
    },
    secondaryText: {
        color: "#2F6BFF",
    },
    camera: {
        flex: 1,
    },
    cameraOverlay: {
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        justifyContent: "space-between",
    },
    cameraHeader: {
        padding: 24,
        alignItems: "flex-end",
    },
    closeButton: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: "rgba(0,0,0,0.5)",
        justifyContent: "center",
        alignItems: "center",
    },
    closeText: {
        fontSize: 32,
        color: "#fff",
        fontWeight: "600",
    },
    cameraFooter: {
        padding: 24,
        alignItems: "center",
    },
    captureButton: {
        width: 70,
        height: 70,
        borderRadius: 35,
        backgroundColor: "#fff",
        justifyContent: "center",
        alignItems: "center",
        borderWidth: 4,
        borderColor: "#2F6BFF",
    },
    captureButtonInner: {
        width: 54,
        height: 54,
        borderRadius: 27,
        backgroundColor: "#2F6BFF",
    },
    previewImage: {
        width: "100%",
        height: 300,
        borderRadius: 12,
        marginBottom: 16,
        backgroundColor: "#f0f0f0",
    },
    rotateButton: {
        height: 40,
        borderRadius: 8,
        backgroundColor: "#f0f0f0",
        justifyContent: "center",
        alignItems: "center",
        marginBottom: 24,
    },
    rotateButtonText: {
        fontSize: 14,
        fontWeight: "600",
        color: "#333",
    },
    formContainer: {
        marginBottom: 24,
    },
    label: {
        fontSize: 14,
        fontWeight: "600",
        color: "#333",
        marginBottom: 8,
        marginTop: 12,
    },
    input: {
        height: 50,
        borderWidth: 1.5,
        borderColor: "#e0e0e0",
        borderRadius: 12,
        paddingHorizontal: 16,
        fontSize: 16,
        color: "#333",
        backgroundColor: "#fff",
    },
    actionButtons: {
        flexDirection: "row",
        gap: 16,
        marginTop: 8,
    },
});