import { initializeApp, getApp, getApps } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Firebase configuration using environment variables
const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
    measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
};

console.log('🔥 FIREBASE CONFIG CHECK:', {
    apiKey: firebaseConfig.apiKey ? '...' + firebaseConfig.apiKey.slice(-5) : 'MISSING',
    authDomain: firebaseConfig.authDomain,
    projectId: firebaseConfig.projectId,
    appId: firebaseConfig.appId
});

// Initialize Firebase
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
console.log('✅ Firebase App Initialized:', app.name);

// Initialize Auth
let auth;
try {
    auth = getAuth(app);
    console.log('🛡️ Firebase Auth Initialized');
} catch (error) {
    console.error('❌ Error initializing Firebase Auth:', error);
    throw error;
}

export { auth };
export const googleProvider = new GoogleAuthProvider();

export default app;
