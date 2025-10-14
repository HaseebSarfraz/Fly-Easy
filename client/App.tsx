import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import LandingPageScreen from "./src/screens/Landing-page/LandingPage";
import HotelSearchScreen from "./src/screens/Hotels/HotelSearchScreen";
import RestaurantSearchScreen from "./src/screens/Restaurants/RestaurantSearchScreen";
import RestaurantListScreen from "./src/screens/Restaurants/RestaurantListScreen";

const Stack = createNativeStackNavigator();

export default function App() {
    return (
        <NavigationContainer>
            <Stack.Navigator>
                <Stack.Screen name="LandingPage" component={LandingPageScreen} />
                <Stack.Screen name="HotelSearch" component={HotelSearchScreen} />
                <Stack.Screen name="RestaurantsSearch" component={RestaurantSearchScreen} />
                <Stack.Screen name="RestaurantList" component={RestaurantListScreen} />
            </Stack.Navigator>
        </NavigationContainer>
    );
}
