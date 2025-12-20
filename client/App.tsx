// App.tsx
import React, { useState } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import HotelResultsScreen from "./src/screens/Hotels/HotelResultsScreen";
import LandingPageScreen from "./src/screens/Landing-page/LandingPage";
import HotelSearchScreen from "./src/screens/Hotels/HotelSearchScreen";
import RestaurantSearchScreen from "./src/screens/Restaurants/RestaurantSearchScreen";
import RestaurantListScreen from "./src/screens/Restaurants/RestaurantListScreen";
import HotelPreferencesScreen from "./src/screens/Hotels/HotelPreferencesScreen";
import DigitalWalletScreen from "./src/screens/Wallet/DigitalWalletScreen";
import Scanner from "./src/components/wallet-components/Scanner";
import AirportTracker from "./src/screens/AirportTracker/AirportTracker";
import LoginPageScreen from "./src/screens/Login/LoginScreen";
import LoginPage from "./src/screens/Login/LoginPage";
import SignUpPageScreen from "./src/screens/Login/SignUpPage";
import SplashAnimation from "./src/screens/StartAnimation/SplashAnimation";
import EventPreferencesScreen from "./src/screens/EventPlanner/EventPreferences";
import EventSchedulerScreen from "./src/screens/EventPlanner/EventScheduler";


export type RootStackParamList = {
  LandingPage: undefined;
  LoginScreen: undefined;
  LoginPage: undefined;
  SignUpPage: undefined;
  HotelSearch: undefined;
  AirportTracker: undefined;
  RestaurantsSearch: undefined;
  RestaurantList: {
    // SEARCH PARAMS FROM FIRST PAGE
    iata: string;
    airport: string;
    terminal: string;
    food_category: string;
    cuisine: string; 
    dietary_restriction: string;
    // FILTER AND SORT PARAMS FROM SECOND PAGE
    restaurant: string;
    max_distance: number;
    prep_time: number;
    min_rating: number;
    max_price: number;
    p_sort: number;
    d_sort: number;
    r_sort: number;
    t_sort: number;
    wants_open: boolean;
  };
  HotelPreferences: {
    location: string; travellers: number; checkIn: string; checkOut: string;
  };
  HotelResults: {
    location: string;
    travellers: number;
    checkIn: string;
    checkOut: string;
    budgetMin?: number;
    budgetMax?: number;
    minRating?: number;
    cancellation?: "24h" | "48h" | "Free" | "Any";
    payment?: "Online" | "In-person" | "Any";
  };
  DigitalWallet: undefined;
  BoardingPassScanner: {
    onSave?: () => void;
  };
  EventPreferences: undefined;
  
  EventScheduler: {
    preferences: any;
  };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
    const [showSplash, setShowSplash] = useState(true);

    if (showSplash) {
      return <SplashAnimation onFinish={() => setShowSplash(false)} />;
    }
    return (
        <NavigationContainer>
            <Stack.Navigator
                initialRouteName="LoginScreen"
            >
                <Stack.Screen name="LoginScreen" component={LoginPageScreen} />
                <Stack.Screen name="LoginPage" component={LoginPage} />
                <Stack.Screen name="SignUpPage" component={SignUpPageScreen} />
                <Stack.Screen name="LandingPage" component={LandingPageScreen} options={{title: "FlyEasy"}}/>
                <Stack.Screen name="HotelSearch" component={HotelSearchScreen} options={{title: "Search Hotels"}} />
                <Stack.Screen name="RestaurantsSearch" component={RestaurantSearchScreen} options={{title: "Search Restaurants"}}/>
                <Stack.Screen name="RestaurantList" component={RestaurantListScreen} options={{title: "Restaurants"}}/>
                <Stack.Screen name="HotelPreferences" component={HotelPreferencesScreen} options={{title: "Select Preferences"}}/>
                <Stack.Screen name="HotelResults" component={HotelResultsScreen} options={{title: "Hotels"}}/>
                <Stack.Screen 
                    name="DigitalWallet" 
                    component={DigitalWalletScreen}
                    options={{ title: "Digital Wallet" }}
                />
                <Stack.Screen 
                    name="BoardingPassScanner" 
                    component={Scanner}
                    options={{ title: "Scan Boarding Pass" }}
                />
                <Stack.Screen 
                    name="AirportTracker" 
                    component={AirportTracker}
                    options={{ title: "Airport Tracker" }}
                />
                <Stack.Screen 
                    name="EventPreferences" 
                    component={EventPreferencesScreen}
                    options={{ title: "Event Planner" }}
                />
                <Stack.Screen 
                    name="EventScheduler" 
                    component={EventSchedulerScreen}
                    options={{ title: "Your Itinerary" }}
                />
            </Stack.Navigator>
        </NavigationContainer>
    );
}