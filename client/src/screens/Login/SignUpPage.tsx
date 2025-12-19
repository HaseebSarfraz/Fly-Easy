// src/screens/Login/SignUpPage.tsx
import React, { useState } from "react";
import {
    SafeAreaView,
    Text,
    StyleSheet,
    View,
    Pressable,
    TextInput,
    ActivityIndicator,
} from "react-native";

import { auth, db } from "../../firebaseConfig";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { doc, setDoc } from "firebase/firestore";

export default function SignUpPageScreen({ navigation }: any) {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showLoginLink, setShowLoginLink] = useState(false);


    const handleSignUp = async () => {
        if (!name || !email || !password) {
            setError("Please fill out all fields.");
            return;
        }

        setLoading(true);
        setError(null);
        setShowLoginLink(false);

        try {
            const userCredential =
                await createUserWithEmailAndPassword(auth, email.trim(), password);

            navigation.replace("LandingPage");

            setDoc(doc(db, "users", userCredential.user.uid), {
                name,
                email: email.trim(),
            }).catch(console.warn);

        } catch (error: any) {
        if (error.code === "auth/email-already-in-use") {
            setError("An account already exists with this email.");
            setShowLoginLink(true);
        } else {
            setError("Signup failed. Try again.");
            setShowLoginLink(false);
        }
    } finally {
            setLoading(false);
        }
    };



    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.container}>
                <Text style={styles.title}>Create Your Account</Text>

                <TextInput
                    style={styles.input}
                    placeholder="Full Name"
                    value={name}
                    onChangeText={setName}
                />
                <TextInput
                    style={styles.input}
                    placeholder="Email"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    value={email}
                    onChangeText={setEmail}
                />
                <TextInput
                    style={styles.input}
                    placeholder="Password"
                    secureTextEntry
                    value={password}
                    onChangeText={setPassword}
                />

                {error && <Text style={styles.error}>{error}</Text>}

                {showLoginLink && (
                    <Pressable onPress={() => navigation.replace("LoginPage")}>
                        <Text style={styles.link}>Go to Login</Text>
                    </Pressable>
                )}


                <Pressable
                    style={[styles.button, styles.primaryButton]}
                    onPress={handleSignUp}
                    disabled={loading}
                >
                    {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Sign Up</Text>}
                </Pressable>
            </View>
        </SafeAreaView>
    );
}

const styles
    =
    StyleSheet.create({
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
