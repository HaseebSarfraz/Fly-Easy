import React, { useState, useRef } from "react";
import {
    SafeAreaView,
    Text,
    StyleSheet,
    View,
    Pressable,
    Image,
    Alert,
} from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import * as ImageManipulator from "expo-image-manipulator";
import * as FileSystem from "expo-file-system";

// @ts-ignore
export default function BoardingPassScannerScreen({ navigation, route }) {
    const [permission, requestPermission] = useCameraPermissions();
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [isCameraActive, setIsCameraActive] = useState(false);
    const cameraRef = useRef<any>(null);

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

    const editImage = async () => {
        if (!capturedImage) return;

        try {
            // Launch the built-in image editor with crop capability
            const result = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ["images"],
                allowsEditing: true,
                quality: 1,
                base64: false,
            });

            // If user didn't cancel, use the edited version
            if (!result.canceled && result.assets[0]) {
                setCapturedImage(result.assets[0].uri);
            }
        } catch (error) {
            console.error("Error editing:", error);
            Alert.alert("Error", "Failed to edit image");
        }
    };

    const openImageManipulator = async () => {
        if (!capturedImage) return;

        try {
            // Use expo-image-manipulator's edit method
            const result = await ImageManipulator.manipulateAsync(
                capturedImage,
                [],
                { compress: 1, format: ImageManipulator.SaveFormat.JPEG }
            );
            
            // For now, just open image picker with editing enabled
            const editResult = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ["images"],
                allowsEditing: true,
                aspect: [4, 3],
                quality: 1,
            });

            if (!editResult.canceled && editResult.assets[0]) {
                setCapturedImage(editResult.assets[0].uri);
            }
        } catch (error) {
            console.error("Error manipulating:", error);
            Alert.alert("Info", "Crop feature coming soon! Use rotate for now.");
        }
    };

    const saveBoardingPass = async () => {
        if (!capturedImage) return;

        try {
            // Use the same path structure as DigitalWallet
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

            // Save metadata - IMPORTANT: imageUri must be the full path
            const metadata = {
                id,
                imageUri: imageUri, // Full path to the image
                timestamp: new Date().toISOString(),
                notes: "Boarding Pass",
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
            <SafeAreaView style={styles.safe}>
                <CameraView style={styles.camera} ref={cameraRef}>
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
                </CameraView>
            </SafeAreaView>
        );
    }

    if (capturedImage) {
        return (
            <SafeAreaView style={styles.safe}>
                <View style={styles.container}>
                    <Text style={styles.title}>Preview & Adjust</Text>

                    <Image 
                        source={{ uri: capturedImage }} 
                        style={styles.previewImage}
                        resizeMode="contain"
                    />

                    <View style={styles.adjustButtons}>
                        <Pressable style={styles.adjustButton} onPress={rotateImage}>
                            <Text style={styles.adjustButtonText}>🔄 Rotate</Text>
                        </Pressable>
                    </View>

                    <Text style={styles.cropNote}>
                        Tip: Use gallery picker with editing enabled for cropping
                    </Text>

                    <View style={styles.actionButtons}>
                        <Pressable
                            style={[styles.button, styles.secondaryButton]}
                            onPress={() => setCapturedImage(null)}
                        >
                            <Text style={[styles.buttonText, styles.secondaryText]}>
                                Retake
                            </Text>
                        </Pressable>
                        <Pressable
                            style={[styles.button, styles.primaryButton]}
                            onPress={saveBoardingPass}
                        >
                            <Text style={styles.buttonText}>Save</Text>
                        </Pressable>
                    </View>
                </View>
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
        flex: 1,
        backgroundColor: "transparent",
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
        height: 400,
        borderRadius: 12,
        marginBottom: 16,
        backgroundColor: "#f0f0f0",
    },
    adjustButtons: {
        flexDirection: "row",
        gap: 16,
        marginBottom: 8,
    },
    adjustButton: {
        flex: 1,
        height: 50,
        borderRadius: 12,
        backgroundColor: "#f0f0f0",
        justifyContent: "center",
        alignItems: "center",
    },
    adjustButtonText: {
        fontSize: 16,
        fontWeight: "600",
        color: "#333",
    },
    cropNote: {
        fontSize: 12,
        color: "#999",
        textAlign: "center",
        marginBottom: 16,
        fontStyle: "italic",
    },
    actionButtons: {
        flexDirection: "row",
        gap: 16,
    },
});