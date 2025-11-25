import React, { useEffect, useRef } from 'react';
import { View, Animated, StyleSheet, Dimensions, Text, Easing } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function SplashAnimation({ onFinish }: { onFinish: () => void }) {
  const planeX = useRef(new Animated.Value(-100)).current;
  const textOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const playAnimation = async () => {
      const { sound } = await Audio.Sound.createAsync(
        require('../../../assets/swoosh.mp3')
      );

      // Animate plane left to right
      Animated.timing(planeX, {
        toValue: SCREEN_WIDTH + 100,
        duration: 1500,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
        }).start();

      // Play sound
      await sound.playAsync();

      // Fade in text after 800ms
      setTimeout(() => {
        Animated.timing(textOpacity, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }).start(() => {
          setTimeout(() => {
            sound.unloadAsync();
            onFinish();
          }, 1000);
        });
      }, 800);
    };

    playAnimation();
  }, []);

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.plane, { transform: [{ translateX: planeX }], left: 0}]}>
        <Ionicons name="airplane-sharp" size={60} color="#2F6BFF" />
      </Animated.View>
      
      <Animated.Text style={[styles.text, { opacity: textOpacity }]}>
        Fly Easy
      </Animated.Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  plane: {
    position: 'absolute',
  },
  text: {
    fontSize: 48,
    fontWeight: '700',
    color: '#2F6BFF',
    marginLeft: 20,
  },
});