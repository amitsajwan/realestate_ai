import React, { useRef, useState } from 'react';
import { Animated, Pressable, StyleSheet, View } from 'react-native';
import { Card, Surface } from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import GestureUtils from '../utils/gestureUtils';
import { useBranding } from '../contexts/BrandingContext';

export default function InteractiveCard({
  children,
  onPress,
  onLongPress,
  style,
  elevation = 4,
  gradient = false,
  gradientColors,
  hapticFeedback = true,
  animationType = 'scale', // scale, lift, bounce
  swipeEnabled = false,
  onSwipeLeft,
  onSwipeRight,
  borderRadius = 12,
  disabled = false,
  ...props
}) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const translateYAnim = useRef(new Animated.Value(0)).current;
  const translateXAnim = useRef(new Animated.Value(0)).current;
  const [isPressed, setIsPressed] = useState(false);
  
  const { branding } = useBranding();

  const handlePressIn = () => {
    if (disabled) return;
    
    setIsPressed(true);
    
    if (hapticFeedback) {
      GestureUtils.haptics.light();
    }

    switch (animationType) {
      case 'scale':
        Animated.timing(scaleAnim, {
          toValue: 0.98,
          duration: 150,
          useNativeDriver: true,
        }).start();
        break;
      case 'lift':
        Animated.timing(translateYAnim, {
          toValue: -4,
          duration: 150,
          useNativeDriver: true,
        }).start();
        break;
      case 'bounce':
        Animated.timing(scaleAnim, {
          toValue: 0.95,
          duration: 100,
          useNativeDriver: true,
        }).start();
        break;
    }
  };

  const handlePressOut = () => {
    if (disabled) return;
    
    setIsPressed(false);

    switch (animationType) {
      case 'scale':
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 150,
          useNativeDriver: true,
        }).start();
        break;
      case 'lift':
        Animated.timing(translateYAnim, {
          toValue: 0,
          duration: 150,
          useNativeDriver: true,
        }).start();
        break;
      case 'bounce':
        Animated.spring(scaleAnim, {
          toValue: 1,
          friction: 4,
          useNativeDriver: true,
        }).start();
        break;
    }
  };

  const handlePress = () => {
    if (disabled) return;
    
    if (hapticFeedback) {
      GestureUtils.haptics.medium();
    }
    
    onPress && onPress();
  };

  const handleLongPress = () => {
    if (disabled) return;
    
    GestureUtils.gestures.handleLongPress(() => {
      onLongPress && onLongPress();
    }, hapticFeedback);
  };

  const handleSwipeGesture = (gestureState) => {
    if (!swipeEnabled || disabled) return;
    
    GestureUtils.gestures.handleSwipe(
      gestureState,
      onSwipeLeft,
      onSwipeRight,
      null,
      null
    );
  };

  const getCardStyle = () => {
    return [
      {
        borderRadius,
        overflow: 'hidden',
      },
      style,
    ];
  };

  const getAnimatedStyle = () => {
    return {
      transform: [
        { scale: scaleAnim },
        { translateY: translateYAnim },
        { translateX: translateXAnim },
      ],
    };
  };

  const CardContent = ({ children }) => {
    if (gradient) {
      return (
        <LinearGradient
          colors={gradientColors || [branding.primaryColor, branding.secondaryColor]}
          style={styles.gradientContent}
        >
          {children}
        </LinearGradient>
      );
    }
    
    return (
      <View style={styles.content}>
        {children}
      </View>
    );
  };

  if (onPress || onLongPress || swipeEnabled) {
    return (
      <Animated.View style={[getAnimatedStyle(), getCardStyle()]}>
        <Surface
          elevation={isPressed ? elevation + 2 : elevation}
          style={[styles.surface, { borderRadius }]}
        >
          <Pressable
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            onPress={handlePress}
            onLongPress={handleLongPress}
            disabled={disabled}
            style={({ pressed }) => [
              styles.pressable,
              {
                opacity: pressed ? 0.95 : 1,
              },
            ]}
            {...(swipeEnabled && {
              onMoveShouldSetResponder: () => true,
              onResponderMove: (evt) => {
                // Handle swipe gesture
                const { dx, dy } = evt.nativeEvent;
                if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 10) {
                  Animated.timing(translateXAnim, {
                    toValue: dx * 0.1,
                    duration: 0,
                    useNativeDriver: true,
                  }).start();
                }
              },
              onResponderRelease: (evt) => {
                const { dx, dy, vx } = evt.nativeEvent;
                handleSwipeGesture({ dx, dy, vx });
                
                // Reset position
                Animated.spring(translateXAnim, {
                  toValue: 0,
                  friction: 6,
                  useNativeDriver: true,
                }).start();
              },
            })}
          >
            <CardContent>
              {children}
            </CardContent>
          </Pressable>
        </Surface>
      </Animated.View>
    );
  }

  return (
    <Animated.View style={[getAnimatedStyle(), getCardStyle()]}>
      <Surface elevation={elevation} style={[styles.surface, { borderRadius }]}>
        <CardContent>
          {children}
        </CardContent>
      </Surface>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  surface: {
    flex: 1,
  },
  pressable: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  gradientContent: {
    flex: 1,
  },
});