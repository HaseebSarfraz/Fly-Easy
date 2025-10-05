// src/screens/Hotels/HotelsScreen.tsx
import React from "react";
import { SafeAreaView, View } from 'react-native';
import CardGrid from "../../components/hotel-components/CardGrid";

export default function HotelsScreen() {
  return (
    <SafeAreaView style={{ flex: 1 }}>
      <View style={{ padding: 16 }}>
        <CardGrid count={3} numColumns={2} gap={12} />
      </View>
    </SafeAreaView>
  );
}


