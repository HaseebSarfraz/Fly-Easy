<<<<<<< Updated upstream
// App.tsx
import React from 'react';
import HotelsScreen from './src/screens/Hotels/HotelsScreen';
import HotelSearchScreen from './src/screens/HotelSearchScreen';

export default function App() {
  return <HotelSearchScreen />;
=======
import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import LandingPageScreen from "./src/screens/Landing-page/LandingPage";
import HotelSearchScreen from "./src/screens/Hotels/HotelSearchScreen";
import RestaurantsScreen from "./src/screens/Restaurants/RestaurantsScreen";
import HotelPreferencesScreen from "./src/screens/Hotels/HotelPreferencesScreen";

type RootStackParamList = {
  LandingPage: undefined;
  HotelSearch: undefined;
  RestaurantsSearch: undefined;
  HotelPreferences: {
    location: string; travellers: number; checkIn: string; checkOut: string;
  };
};

const Stack = createNativeStackNavigator<RootStackParamList>(); // <-- add the generic

export default function App() {
    return (
        <NavigationContainer>
            <Stack.Navigator>
                <Stack.Screen name="LandingPage" component={LandingPageScreen} />
                <Stack.Screen name="HotelSearch" component={HotelSearchScreen} />
                <Stack.Screen name="RestaurantsSearch" component={RestaurantsScreen} />
                <Stack.Screen name="HotelPreferences" component={HotelPreferencesScreen} />
            </Stack.Navigator>
        </NavigationContainer>
    );
>>>>>>> Stashed changes
}

