// App.tsx
import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import HotelResultsScreen from "./src/screens/Hotels/HotelResultsScreen";
import LandingPageScreen from "./src/screens/Landing-page/LandingPage";
import HotelSearchScreen from "./src/screens/Hotels/HotelSearchScreen";
import RestaurantSearchScreen from "./src/screens/Restaurants/RestaurantSearchScreen";
import RestaurantListScreen from "./src/screens/Restaurants/RestaurantListScreen";
import HotelPreferencesScreen from "./src/screens/Hotels/HotelPreferencesScreen";

export type RootStackParamList = {
  LandingPage: undefined;
  HotelSearch: undefined;
  RestaurantsSearch: undefined;
  RestaurantList: {
    iata: string,
    airport: string,
    terminal: string,
    food_category: string,
    cuisine: string, 
    dietary_restriction: string
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
};

const Stack = createNativeStackNavigator<RootStackParamList>(); // <-- add the generic

export default function App() {
    return (
        <NavigationContainer>
            <Stack.Navigator>
                <Stack.Screen name="LandingPage" component={LandingPageScreen} />
                <Stack.Screen name="HotelSearch" component={HotelSearchScreen} />
                <Stack.Screen name="RestaurantsSearch" component={RestaurantSearchScreen} />
                <Stack.Screen name="RestaurantList" component={RestaurantListScreen} />
                <Stack.Screen name="HotelPreferences" component={HotelPreferencesScreen} />
                <Stack.Screen name="HotelResults" component={HotelResultsScreen} />
            </Stack.Navigator>
        </NavigationContainer>
    );
}
