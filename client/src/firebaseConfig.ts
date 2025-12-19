import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { initializeFirestore } from "firebase/firestore";

const firebaseConfig = {
    apiKey: "AIzaSyCZ5GfsJQHJRIC3mCwv-xPXaKKynzgDgJA",
    authDomain: "flyeasyapp-csc392.firebaseapp.com",
    projectId: "flyeasyapp-csc392",
    storageBucket: "flyeasyapp-csc392.firebasestorage.app",
    messagingSenderId: "656942263133",
    appId: "1:656942263133:web:e30d5e4c001003a57956b4",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = initializeFirestore(app, {
    experimentalForceLongPolling: true,
});

