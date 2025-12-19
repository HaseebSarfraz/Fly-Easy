// src/screens/Login/LoginPage.tsx
import React, { useState } from "react";
import { SafeAreaView, Text, StyleSheet, View, TextInput, Pressable, ActivityIndicator } from "react-native";

import { auth } from "../../firebaseConfig";
import { signInWithEmailAndPassword } from "firebase/auth";

export default function LoginPage({ navigation }: any) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showSignupLink, setShowSignupLink] = useState(false);


    const handleLogin = async () => {
        if (!email || !password) {
            setError("Please fill out all fields.");
            return;
        }

        setLoading(true);
        setError(null);
        setShowSignupLink(false);

        try {
            await signInWithEmailAndPassword(auth, email.trim(), password);
            navigation.replace("LandingPage");
        } catch (error: any) {
            if (error.code === "auth/invalid-credential") {
                setError("Email or password is incorrect.");
                setShowSignupLink(true); // user may need to sign up
            } else {
                setError("Login failed. Try again.");
            }
        } finally {
            setLoading(false);
        }
    };



    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.container}>
                <Text style={styles.title}>Login</Text>

                <TextInput style={styles.input} placeholder="Email" value={email} onChangeText={setEmail} autoCapitalize="none" />
                <TextInput style={styles.input} placeholder="Password" value={password} onChangeText={setPassword} secureTextEntry />
                {error && <Text style={styles.error}>{error}</Text>}

                {showSignupLink && (
                    <View style={{ marginTop: 6 }}>
                        <Pressable onPress={() => navigation.replace("SignUpPage")}>
                            <Text style={styles.link}>Create an account</Text>
                        </Pressable>
                    </View>
                )}



                <Pressable style={[styles.button, styles.primaryButton]} onPress={handleLogin} disabled={loading}>
                    {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Login</Text>}
                </Pressable>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safe: { flex: 1, backgroundColor: "#fff" },
    container: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24 },
    title: { fontSize: 28, fontWeight: "700", marginBottom: 24, color: "#2F6BFF" },
    input: { width: "100%", borderColor: "#ccc", borderWidth: 1, borderRadius: 12, padding: 12, marginVertical: 8, fontSize: 16 },
    button: { height: 50, width: "100%", borderRadius: 12, justifyContent: "center", alignItems: "center", marginTop: 20 },
    primaryButton: { backgroundColor: "#2F6BFF" },
    buttonText: { fontSize: 16, fontWeight: "600", color: "#fff" },
    error: {
        color: "#E53935",
        marginTop: 12,
        fontSize: 14,
        textAlign: "center",
    },
    link: {
        color: "#2F6BFF",
        marginTop: 6,
        fontWeight: "600",
        textDecorationLine: "underline",
    },
});
