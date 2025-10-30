import React, { useState, useEffect } from "react";
import {
    Text,
    StyleSheet,
    View,
    Pressable,
    FlatList,
    Image,
    Alert,
    Modal,
    ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import * as FileSystem from "expo-file-system/legacy";
import { NativeStackScreenProps } from "@react-navigation/native-stack";

type RootStackParamList = {
    DigitalWallet: undefined;
    BoardingPassScanner: {
        onSave: () => void;
    };
};

type Props = NativeStackScreenProps<RootStackParamList, 'DigitalWallet'>;

interface BoardingPass {
    id: string;
    imageUri: string;
    passengerName: string;
    flightNumber: string;
    seatNumber?: string;
    gateNumber?: string;
    timestamp: string;
}

export default function DigitalWalletScreen({ navigation }: Props) {
    const [boardingPasses, setBoardingPasses] = useState<BoardingPass[]>([]);
    const [selectedPass, setSelectedPass] = useState<BoardingPass | null>(null);
    const [modalVisible, setModalVisible] = useState(false);

    useEffect(() => {
        loadBoardingPasses();
    }, []);

    const loadBoardingPasses = async () => {
        try {
            const walletDir = (FileSystem as any).documentDirectory + "wallet/";
            console.log("Loading from wallet directory:", walletDir);
            
            const dirInfo = await FileSystem.getInfoAsync(walletDir);
            console.log("Directory exists:", dirInfo.exists);

            if (!dirInfo.exists) {
                console.log("Creating wallet directory...");
                await FileSystem.makeDirectoryAsync(walletDir, { intermediates: true });
                return;
            }

            const files = await FileSystem.readDirectoryAsync(walletDir);
            console.log("Files in wallet directory:", files);
            
            const passes = files
                .filter((f) => f.endsWith(".json"))
                .map((f) => f.replace(".json", ""));

            console.log("JSON files found:", passes);

            const passData = await Promise.all(
                passes.map(async (id) => {
                    const jsonUri = walletDir + id + ".json";
                    console.log("Reading file:", jsonUri);
                    const content = await FileSystem.readAsStringAsync(jsonUri);
                    const parsed = JSON.parse(content);
                    console.log("Parsed data:", parsed);
                    return parsed;
                })
            );

            console.log("Total boarding passes loaded:", passData.length);
            setBoardingPasses(passData);
        } catch (error) {
            console.error("Error loading boarding passes:", error);
        }
    };

    const deleteBoardingPass = async (id: string, passengerName: string) => {
        Alert.alert(
            "Delete Boarding Pass",
            `Are you sure you want to delete the boarding pass for ${passengerName}?`,
            [
                { text: "Cancel", style: "cancel" },
                {
                    text: "Delete",
                    style: "destructive",
                    onPress: async () => {
                        try {
                            const walletDir = (FileSystem as any).documentDirectory + "wallet/";
                            await FileSystem.deleteAsync(walletDir + id + ".json");
                            await FileSystem.deleteAsync(walletDir + id + ".jpg");
                            loadBoardingPasses();
                        } catch (error) {
                            console.error("Error deleting:", error);
                        }
                    },
                },
            ]
        );
    };

    const openFullImage = (pass: BoardingPass) => {
        setSelectedPass(pass);
        setModalVisible(true);
    };

    const renderBoardingPass = ({ item }: { item: BoardingPass }) => {
        console.log("Rendering boarding pass:", item.id, "Image URI:", item.imageUri);
        
        return (
            <Pressable 
                style={styles.passCard}
                onPress={() => openFullImage(item)}
            >
                <Image 
                    source={{ uri: item.imageUri }} 
                    style={styles.passImage}
                    onError={(error) => {
                        console.error("Image load error for", item.id, error.nativeEvent);
                    }}
                    onLoad={() => {
                        console.log("Image loaded successfully for", item.id);
                    }}
                />
                <View style={styles.passInfo}>
                    <Text style={styles.passName}>{item.passengerName}</Text>
                    <Text style={styles.passFlight}>Flight: {item.flightNumber}</Text>
                    {item.seatNumber && (
                        <Text style={styles.passDetail}>Seat: {item.seatNumber}</Text>
                    )}
                    {item.gateNumber && (
                        <Text style={styles.passDetail}>Gate: {item.gateNumber}</Text>
                    )}
                    <Text style={styles.passDate}>
                        {new Date(item.timestamp).toLocaleDateString()}
                    </Text>
                </View>
                <Pressable
                    style={styles.deleteButton}
                    onPress={(e) => {
                        e.stopPropagation();
                        deleteBoardingPass(item.id, item.passengerName);
                    }}
                >
                    <Text style={styles.deleteText}>×</Text>
                </Pressable>
            </Pressable>
        );
    };

    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.container}>
                <Text style={styles.title}>Digital Wallet</Text>
                <Text style={styles.subtitle}>Your saved boarding passes</Text>

                {boardingPasses.length === 0 ? (
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No boarding passes yet</Text>
                        <Text style={styles.emptySubtext}>
                            Tap the button below to add your first one
                        </Text>
                    </View>
                ) : (
                    <FlatList
                        data={boardingPasses}
                        renderItem={renderBoardingPass}
                        keyExtractor={(item) => item.id}
                        style={styles.list}
                        contentContainerStyle={styles.listContent}
                    />
                )}

                <Pressable
                    style={styles.addButton}
                    onPress={() => {
                        navigation.navigate("BoardingPassScanner", {
                            onSave: loadBoardingPasses,
                        });
                    }}
                >
                    <Text style={styles.addButtonText}>+ Add Boarding Pass</Text>
                </Pressable>
            </View>

            {/* Full Image Modal */}
            <Modal
                visible={modalVisible}
                transparent={true}
                animationType="fade"
                onRequestClose={() => setModalVisible(false)}
            >
                <View style={styles.modalContainer}>
                    <Pressable 
                        style={styles.modalBackdrop}
                        onPress={() => setModalVisible(false)}
                    />
                    <View style={styles.modalContent}>
                        <Pressable
                            style={styles.modalClose}
                            onPress={() => setModalVisible(false)}
                        >
                            <Text style={styles.modalCloseText}>×</Text>
                        </Pressable>
                        
                        {selectedPass && (
                            <ScrollView 
                                contentContainerStyle={styles.modalScroll}
                                maximumZoomScale={3}
                                minimumZoomScale={1}
                                showsHorizontalScrollIndicator={false}
                                showsVerticalScrollIndicator={false}
                            >
                                <Image
                                    source={{ uri: selectedPass.imageUri }}
                                    style={styles.fullImage}
                                    resizeMode="contain"
                                />
                            </ScrollView>
                        )}
                    </View>
                </View>
            </Modal>
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
    },
    title: {
        fontSize: 32,
        fontWeight: "700",
        marginBottom: 8,
        color: "#2F6BFF",
    },
    subtitle: {
        fontSize: 16,
        fontWeight: "500",
        color: "#555",
        marginBottom: 24,
    },
    emptyState: {
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
    },
    emptyText: {
        fontSize: 18,
        fontWeight: "600",
        color: "#999",
        marginBottom: 8,
    },
    emptySubtext: {
        fontSize: 14,
        color: "#999",
        textAlign: "center",
    },
    list: {
        flex: 1,
    },
    listContent: {
        gap: 16,
    },
    passCard: {
        backgroundColor: "#f9f9f9",
        borderRadius: 12,
        padding: 16,
        flexDirection: "row",
        alignItems: "center",
        borderWidth: 1,
        borderColor: "#e0e0e0",
    },
    passImage: {
        width: 80,
        height: 80,
        borderRadius: 8,
        marginRight: 16,
        backgroundColor: "#e0e0e0",
    },
    passInfo: {
        flex: 1,
    },
    passName: {
        fontSize: 16,
        fontWeight: "700",
        color: "#333",
        marginBottom: 4,
    },
    passFlight: {
        fontSize: 14,
        fontWeight: "600",
        color: "#2F6BFF",
        marginBottom: 4,
    },
    passDetail: {
        fontSize: 13,
        color: "#666",
        marginBottom: 2,
    },
    passDate: {
        fontSize: 12,
        color: "#999",
        marginTop: 4,
    },
    deleteButton: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: "#ff4444",
        justifyContent: "center",
        alignItems: "center",
    },
    deleteText: {
        fontSize: 24,
        color: "#fff",
        fontWeight: "600",
    },
    addButton: {
        height: 50,
        borderRadius: 12,
        backgroundColor: "#2F6BFF",
        justifyContent: "center",
        alignItems: "center",
        marginTop: 16,
    },
    addButtonText: {
        fontSize: 16,
        fontWeight: "600",
        color: "#fff",
    },
    modalContainer: {
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
    },
    modalBackdrop: {
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.9)",
    },
    modalContent: {
        width: "90%",
        maxHeight: "90%",
        backgroundColor: "#fff",
        borderRadius: 12,
        overflow: "hidden",
    },
    modalClose: {
        position: "absolute",
        top: 8,
        right: 8,
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 10,
    },
    modalCloseText: {
        fontSize: 32,
        color: "#fff",
        fontWeight: "600",
    },
    modalScroll: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    },
    fullImage: {
        width: "100%",
        height: 600,
    },
    modalDetails: {
        width: "100%",
        padding: 16,
        backgroundColor: "#f9f9f9",
        borderRadius: 12,
    },
    modalName: {
        fontSize: 20,
        fontWeight: "700",
        color: "#333",
        marginBottom: 8,
    },
    modalFlight: {
        fontSize: 18,
        fontWeight: "600",
        color: "#2F6BFF",
        marginBottom: 8,
    },
    modalDetail: {
        fontSize: 16,
        color: "#666",
        marginBottom: 4,
    },
});