import * as Haptics from 'expo-haptics';
import { Animated } from 'react-native';

export const GestureUtils = {
  // Haptic feedback patterns
  haptics: {
    light: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
    medium: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium),
    heavy: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy),
    success: () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success),
    warning: () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning),
    error: () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error),
  },

  // Common animations
  animations: {
    // Button press animation
    buttonPress: (scaleAnim, callback) => {
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 0.95,
          duration: 100,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 100,
          useNativeDriver: true,
        }),
      ]).start(callback);
    },

    // Card tap animation
    cardTap: (scaleAnim, callback) => {
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 0.98,
          duration: 150,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 150,
          useNativeDriver: true,
        }),
      ]).start(callback);
    },

    // Slide in from right
    slideInRight: (translateAnim, duration = 300) => {
      return Animated.timing(translateAnim, {
        toValue: 0,
        duration,
        useNativeDriver: true,
      });
    },

    // Slide out to left
    slideOutLeft: (translateAnim, duration = 300) => {
      return Animated.timing(translateAnim, {
        toValue: -100,
        duration,
        useNativeDriver: true,
      });
    },

    // Fade in
    fadeIn: (opacityAnim, duration = 300) => {
      return Animated.timing(opacityAnim, {
        toValue: 1,
        duration,
        useNativeDriver: true,
      });
    },

    // Fade out
    fadeOut: (opacityAnim, duration = 300) => {
      return Animated.timing(opacityAnim, {
        toValue: 0,
        duration,
        useNativeDriver: true,
      });
    },

    // Scale bounce
    scaleBounce: (scaleAnim, callback) => {
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 1.1,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.spring(scaleAnim, {
          toValue: 1,
          friction: 3,
          useNativeDriver: true,
        }),
      ]).start(callback);
    },

    // Shake animation for errors
    shake: (translateAnim) => {
      return Animated.sequence([
        Animated.timing(translateAnim, { toValue: -10, duration: 100, useNativeDriver: true }),
        Animated.timing(translateAnim, { toValue: 10, duration: 100, useNativeDriver: true }),
        Animated.timing(translateAnim, { toValue: -5, duration: 100, useNativeDriver: true }),
        Animated.timing(translateAnim, { toValue: 0, duration: 100, useNativeDriver: true }),
      ]);
    },

    // Pulse animation
    pulse: (scaleAnim, callback) => {
      return Animated.loop(
        Animated.sequence([
          Animated.timing(scaleAnim, {
            toValue: 1.05,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(scaleAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
    },
  },

  // Gesture handlers
  gestures: {
    // Swipe gesture handler
    handleSwipe: (gestureState, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown) => {
      const { dx, dy, vx, vy } = gestureState;
      const minSwipeDistance = 50;
      const minSwipeVelocity = 0.3;

      if (Math.abs(dx) > Math.abs(dy)) {
        // Horizontal swipe
        if (dx > minSwipeDistance || vx > minSwipeVelocity) {
          // Swipe right
          onSwipeRight && onSwipeRight();
          GestureUtils.haptics.light();
        } else if (dx < -minSwipeDistance || vx < -minSwipeVelocity) {
          // Swipe left
          onSwipeLeft && onSwipeLeft();
          GestureUtils.haptics.light();
        }
      } else {
        // Vertical swipe
        if (dy > minSwipeDistance || vy > minSwipeVelocity) {
          // Swipe down
          onSwipeDown && onSwipeDown();
          GestureUtils.haptics.light();
        } else if (dy < -minSwipeDistance || vy < -minSwipeVelocity) {
          // Swipe up
          onSwipeUp && onSwipeUp();
          GestureUtils.haptics.light();
        }
      }
    },

    // Long press handler
    handleLongPress: (callback, hapticFeedback = true) => {
      if (hapticFeedback) {
        GestureUtils.haptics.medium();
      }
      callback && callback();
    },

    // Double tap handler
    handleDoubleTap: (callback, hapticFeedback = true) => {
      if (hapticFeedback) {
        GestureUtils.haptics.light();
      }
      callback && callback();
    },
  },

  // Micro-interactions
  microInteractions: {
    // Loading state with pulse
    showLoading: (scaleAnim) => {
      return GestureUtils.animations.pulse(scaleAnim);
    },

    // Success feedback
    showSuccess: (scaleAnim, callback) => {
      GestureUtils.haptics.success();
      GestureUtils.animations.scaleBounce(scaleAnim, callback);
    },

    // Error feedback
    showError: (translateAnim, callback) => {
      GestureUtils.haptics.error();
      GestureUtils.animations.shake(translateAnim).start(callback);
    },

    // Form field focus
    focusField: (scaleAnim, callback) => {
      GestureUtils.haptics.light();
      Animated.timing(scaleAnim, {
        toValue: 1.02,
        duration: 200,
        useNativeDriver: true,
      }).start(callback);
    },

    // Form field blur
    blurField: (scaleAnim, callback) => {
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }).start(callback);
    },
  },

  // Transition helpers
  transitions: {
    // Screen transition
    screenTransition: (fadeAnim, slideAnim, callback) => {
      Animated.parallel([
        GestureUtils.animations.fadeIn(fadeAnim, 400),
        GestureUtils.animations.slideInRight(slideAnim, 400),
      ]).start(callback);
    },

    // Modal transition
    modalTransition: (scaleAnim, fadeAnim, callback) => {
      Animated.parallel([
        Animated.spring(scaleAnim, {
          toValue: 1,
          friction: 6,
          useNativeDriver: true,
        }),
        GestureUtils.animations.fadeIn(fadeAnim, 300),
      ]).start(callback);
    },

    // Tab transition
    tabTransition: (fadeAnim, callback) => {
      Animated.sequence([
        GestureUtils.animations.fadeOut(fadeAnim, 150),
        GestureUtils.animations.fadeIn(fadeAnim, 150),
      ]).start(callback);
    },
  },
};

export default GestureUtils;