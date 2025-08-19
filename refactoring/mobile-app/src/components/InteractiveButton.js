import React, { useRef } from 'react';
import { Animated, Pressable, StyleSheet } from 'react-native';
import { Button, Surface } from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import GestureUtils from '../utils/gestureUtils';
import { useBranding } from '../contexts/BrandingContext';

export default function InteractiveButton({
  children,
  onPress,
  style,
  variant = 'primary', // primary, secondary, outline, ghost
  size = 'medium', // small, medium, large
  disabled = false,
  loading = false,
  icon,
  hapticFeedback = true,
  animationType = 'scale', // scale, bounce, pulse
  ...props
}) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const { branding } = useBranding();

  const handlePressIn = () => {
    if (disabled || loading) return;
    
    if (hapticFeedback) {
      GestureUtils.haptics.light();
    }

    switch (animationType) {
      case 'scale':
        Animated.timing(scaleAnim, {
          toValue: 0.95,
          duration: 100,
          useNativeDriver: true,
        }).start();
        break;
      case 'bounce':
        Animated.timing(scaleAnim, {
          toValue: 0.92,
          duration: 100,
          useNativeDriver: true,
        }).start();
        break;
      case 'pulse':
        GestureUtils.animations.pulse(scaleAnim);
        break;
    }
  };

  const handlePressOut = () => {
    if (disabled || loading) return;

    if (animationType === 'bounce') {
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 3,
        useNativeDriver: true,
      }).start();
    } else {
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      }).start();
    }
  };

  const handlePress = () => {
    if (disabled || loading) return;
    
    if (hapticFeedback) {
      GestureUtils.haptics.medium();
    }
    
    onPress && onPress();
  };

  const getButtonStyle = () => {
    const baseStyle = {
      borderRadius: size === 'small' ? 8 : size === 'large' ? 16 : 12,
      minHeight: size === 'small' ? 36 : size === 'large' ? 56 : 48,
    };

    switch (variant) {
      case 'primary':
        return {
          ...baseStyle,
          backgroundColor: branding.primaryColor,
        };
      case 'secondary':
        return {
          ...baseStyle,
          backgroundColor: branding.secondaryColor,
        };
      case 'outline':
        return {
          ...baseStyle,
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderColor: branding.primaryColor,
        };
      case 'ghost':
        return {
          ...baseStyle,
          backgroundColor: 'transparent',
        };
      default:
        return baseStyle;
    }
  };

  const getContentStyle = () => {
    return {
      paddingVertical: size === 'small' ? 6 : size === 'large' ? 16 : 12,
      paddingHorizontal: size === 'small' ? 12 : size === 'large' ? 24 : 16,
    };
  };

  const getTextColor = () => {
    if (variant === 'outline' || variant === 'ghost') {
      return branding.primaryColor;
    }
    return 'white';
  };

  if (variant === 'primary' || variant === 'secondary') {
    return (
      <Animated.View
        style={[
          style,
          {
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        <Pressable
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          onPress={handlePress}
          disabled={disabled || loading}
          style={({ pressed }) => [
            getButtonStyle(),
            {
              opacity: pressed ? 0.9 : 1,
            },
          ]}
        >
          <LinearGradient
            colors={
              variant === 'primary'
                ? [branding.primaryColor, branding.secondaryColor]
                : [branding.secondaryColor, branding.accentColor]
            }
            style={[styles.gradient, getContentStyle()]}
          >
            <Button
              {...props}
              mode="text"
              loading={loading}
              disabled={disabled}
              textColor={getTextColor()}
              icon={icon}
              style={styles.transparentButton}
              contentStyle={styles.transparentContent}
            >
              {children}
            </Button>
          </LinearGradient>
        </Pressable>
      </Animated.View>
    );
  }

  return (
    <Animated.View
      style={[
        style,
        {
          transform: [{ scale: scaleAnim }],
        },
      ]}
    >
      <Surface style={getButtonStyle()} elevation={variant === 'ghost' ? 0 : 2}>
        <Pressable
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          onPress={handlePress}
          disabled={disabled || loading}
          style={({ pressed }) => [
            getContentStyle(),
            {
              opacity: pressed ? 0.7 : 1,
            },
          ]}
        >
          <Button
            {...props}
            mode="text"
            loading={loading}
            disabled={disabled}
            textColor={getTextColor()}
            icon={icon}
            style={styles.transparentButton}
            contentStyle={styles.transparentContent}
          >
            {children}
          </Button>
        </Pressable>
      </Surface>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  gradient: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  transparentButton: {
    backgroundColor: 'transparent',
    margin: 0,
  },
  transparentContent: {
    margin: 0,
  },
});