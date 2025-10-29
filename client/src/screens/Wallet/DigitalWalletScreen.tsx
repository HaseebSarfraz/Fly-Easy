import React, { useState, useEffect } from "react";
import {
    SafeAreaView,
    Text,
    StyleSheet,
    View,
    Pressable,
    FlatList,
    Image,
    Alert,
} from "react-native";
import * as FileSystem from "expo-file-system";
import { NativeStackScreenProps } from "@react-navigation/native-stack";

type RootStackParamList = {
    DigitalWallet: undefined;
    BoardingPassScanner: {
        onSave: () => void;
    };
};

type Props = NativeStackScreenProps<RootStackParamList, 'DigitalWallet'>;

export default function DigitalWalletScreen({ navigation }: Props) {
    const [boardingPasses, setBoardingPasses] = useState<any[]>([]);

    useEffect(() => {
        loadBoardingPasses();
    }, []);

    const loadBoardingPasses = async () => {
        try {
            const walletDir = (FileSystem as any).documentDirectory + "wallet/";
            const dirInfo = await FileSystem.getInfoAsync(walletDir);

            if (!dirInfo.exists) {
                await FileSystem.makeDirectoryAsync(walletDir, { intermediates: true });
                return;
            }

            const files = await FileSystem.readDirectoryAsync(walletDir);
            const passes = files
                .filter((f) => f.endsWith(".json"))
                .map((f) => f.replace(".json", ""));

            const passData = await Promise.all(
                passes.map(async (id) => {
                    const jsonUri = walletDir + id + ".json";
                    const content = await FileSystem.readAsStringAsync(jsonUri);
                    return JSON.parse(content);
                })
            );

            setBoardingPasses(passData);
        } catch (error) {
            console.error("Error loading boarding passes:", error);
        }
    };

    const deleteBoardingPass = async (id: string) => {
        Alert.alert(
            "Delete Boarding Pass",
            "Are you sure you want to delete this boarding pass?",
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

    const renderBoardingPass = ({ item }: any) => (
        <Pressable style={styles.passCard}>
            <Image source={{ uri: item.imageUri }} style={styles.passImage} />
            <View style={styles.passInfo}>
                <Text style={styles.passTitle}>Boarding Pass</Text>
                <Text style={styles.passDate}>{new Date(item.timestamp).toLocaleDateString()}</Text>
                {item.notes && <Text style={styles.passNotes}>{item.notes}</Text>}
            </View>
            <Pressable
                style={styles.deleteButton}
                onPress={() => deleteBoardingPass(item.id)}
            >
                <Text style={styles.deleteText}>×</Text>
            </Pressable>
        </Pressable>
    );

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
    },
    passInfo: {
        flex: 1,
    },
    passTitle: {
        fontSize: 16,
        fontWeight: "600",
        color: "#333",
        marginBottom: 4,
    },
    passDate: {
        fontSize: 14,
        color: "#666",
        marginBottom: 4,
    },
    passNotes: {
        fontSize: 12,
        color: "#999",
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
});