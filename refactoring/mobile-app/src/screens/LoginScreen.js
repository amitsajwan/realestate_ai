import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  Dimensions,
  Pressable,
  StatusBar,
  Animated,
  Keyboard,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Card,
  Divider,
  HelperText,
  IconButton,
  Surface,
  Chip,
  ActivityIndicator,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import * as Haptics from 'expo-haptics';
import * as LocalAuthentication from 'expo-local-authentication';
import { BlurView } from 'expo-blur';
import { useAuth } from '../contexts/AuthContext';
import { useBranding } from '../contexts/BrandingContext';

const { width, height } = Dimensions.get('window');

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [biometricSupported, setBiometricSupported] = useState(false);
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  
  // Animation refs
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const logoAnim = useRef(new Animated.Value(1)).current;

  const { login, register } = useAuth();
  const { branding } = useBranding();

  useEffect(() => {
    // Entry animations
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    // Check biometric support
    checkBiometricSupport();
    
    // Keyboard listeners
    const keyboardWillShow = Keyboard.addListener('keyboardWillShow', () => {
      setKeyboardVisible(true);
      Animated.timing(logoAnim, {
        toValue: 0.7,
        duration: 300,
        useNativeDriver: true,
      }).start();
    });
    
    const keyboardWillHide = Keyboard.addListener('keyboardWillHide', () => {
      setKeyboardVisible(false);
      Animated.timing(logoAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    });

    return () => {
      keyboardWillShow?.remove();
      keyboardWillHide?.remove();
    };
  }, []);

  const checkBiometricSupport = async () => {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    setBiometricSupported(compatible && enrolled);
  };

  const handleBiometricAuth = async () => {
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Sign in to PropertyAI',
        subPrompt: 'Use your biometric to access your account',
        cancelLabel: 'Cancel',
        fallbackLabel: 'Use Password',
      });

      if (result.success) {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        // Auto-login with stored credentials
        navigation.replace('Main');
      }
    } catch (error) {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      console.error('Biometric auth error:', error);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Please enter a valid email';
    }
    
    if (!password.trim()) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    
    if (Object.keys(newErrors).length > 0) {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      // Shake animation for errors
      Animated.sequence([
        Animated.timing(slideAnim, { toValue: -10, duration: 100, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 10, duration: 100, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: -5, duration: 100, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 100, useNativeDriver: true }),
      ]).start();
    }
    
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    try {
      let result;
      if (isLogin) {
        result = await login(email, password);
      } else {
        result = await register({ email, password });
      }

      if (result.success) {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        
        // Success animation
        Animated.parallel([
          Animated.timing(scaleAnim, {
            toValue: 1.1,
            duration: 200,
            useNativeDriver: true,
          }),
          Animated.timing(fadeAnim, {
            toValue: 0.8,
            duration: 200,
            useNativeDriver: true,
          }),
        ]).start(() => {
          if (result.user?.onboardingCompleted) {
            navigation.replace('Main');
          } else {
            navigation.replace('AgentOnboarding');
          }
        });
      } else {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        Alert.alert('Error', result.error);
      }
    } catch (error) {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert('Error', 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = async () => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    // Smooth transition animation
    Animated.sequence([
      Animated.timing(fadeAnim, {
        toValue: 0.5,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
    
    setIsLogin(!isLogin);
    setErrors({});
    setEmail('');
    setPassword('');
  };

  const handleSocialLogin = async (provider) => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    Alert.alert('Coming Soon', `${provider} login will be available soon!`);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={branding.primaryColor} />
      
      {/* Background Gradient */}
      <LinearGradient
        colors={[branding.primaryColor, branding.secondaryColor, branding.accentColor]}
        style={styles.backgroundGradient}
      >
        {/* Animated Background Elements */}
        <Animatable.View
          animation="pulse"
          iterationCount="infinite"
          duration={3000}
          style={[styles.backgroundCircle, styles.circle1]}
        />
        <Animatable.View
          animation="pulse"
          iterationCount="infinite"
          duration={4000}
          delay={1000}
          style={[styles.backgroundCircle, styles.circle2]}
        />
      </LinearGradient>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoid}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Logo Section */}
          <Animated.View
            style={[
              styles.logoSection,
              {
                opacity: fadeAnim,
                transform: [
                  { translateY: slideAnim },
                  { scale: logoAnim },
                ],
              },
            ]}
          >
            <Surface style={styles.logoContainer} elevation={4}>
              <LinearGradient
                colors={['rgba(255,255,255,0.9)', 'rgba(255,255,255,0.7)']}
                style={styles.logoGradient}
              >
                <Text style={styles.logoEmoji}>🏠</Text>
              </LinearGradient>
            </Surface>
            
            <Animatable.Text
              animation="fadeInUp"
              delay={500}
              style={styles.appName}
            >
              PropertyAI
            </Animatable.Text>
            
            <Animatable.Text
              animation="fadeInUp"
              delay={700}
              style={styles.tagline}
            >
              {isLogin ? 'Welcome back!' : 'Join the future of real estate'}
            </Animatable.Text>
          </Animated.View>

          {/* Form Card */}
          <Animated.View
            style={[
              styles.formContainer,
              {
                opacity: fadeAnim,
                transform: [
                  { translateY: slideAnim },
                  { scale: scaleAnim },
                ],
              },
            ]}
          >
            <BlurView intensity={80} style={styles.blurContainer}>
              <Surface style={styles.formCard} elevation={8}>
                {/* Mode Toggle */}
                <View style={styles.modeToggle}>
                  <Pressable
                    onPress={() => !isLogin && toggleMode()}
                    style={[
                      styles.modeButton,
                      isLogin && styles.modeButtonActive,
                    ]}
                  >
                    <Text
                      style={[
                        styles.modeButtonText,
                        isLogin && styles.modeButtonTextActive,
                      ]}
                    >
                      Sign In
                    </Text>
                  </Pressable>
                  <Pressable
                    onPress={() => isLogin && toggleMode()}
                    style={[
                      styles.modeButton,
                      !isLogin && styles.modeButtonActive,
                    ]}
                  >
                    <Text
                      style={[
                        styles.modeButtonText,
                        !isLogin && styles.modeButtonTextActive,
                      ]}
                    >
                      Sign Up
                    </Text>
                  </Pressable>
                </View>

                {/* Form Fields */}
                <View style={styles.form}>
                  <View style={styles.inputContainer}>
                    <TextInput
                      label="Email Address"
                      value={email}
                      onChangeText={setEmail}
                      mode="outlined"
                      keyboardType="email-address"
                      autoCapitalize="none"
                      autoComplete="email"
                      style={styles.input}
                      error={!!errors.email}
                      theme={{ colors: { primary: branding.primaryColor } }}
                      left={<TextInput.Icon icon="email" />}
                    />
                    <HelperText type="error" visible={!!errors.email}>
                      {errors.email}
                    </HelperText>
                  </View>

                  <View style={styles.inputContainer}>
                    <TextInput
                      label="Password"
                      value={password}
                      onChangeText={setPassword}
                      mode="outlined"
                      secureTextEntry={!showPassword}
                      autoComplete="password"
                      style={styles.input}
                      error={!!errors.password}
                      theme={{ colors: { primary: branding.primaryColor } }}
                      left={<TextInput.Icon icon="lock" />}
                      right={
                        <TextInput.Icon
                          icon={showPassword ? 'eye-off' : 'eye'}
                          onPress={() => {
                            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                            setShowPassword(!showPassword);
                          }}
                        />
                      }
                    />
                    <HelperText type="error" visible={!!errors.password}>
                      {errors.password}
                    </HelperText>
                  </View>

                  {/* Biometric Auth Button */}
                  {biometricSupported && isLogin && (
                    <Pressable
                      onPress={handleBiometricAuth}
                      style={styles.biometricButton}
                    >
                      <Surface style={styles.biometricSurface} elevation={2}>
                        <IconButton
                          icon="fingerprint"
                          iconColor={branding.primaryColor}
                          size={24}
                        />
                        <Text style={styles.biometricText}>
                          Use Biometric
                        </Text>
                      </Surface>
                    </Pressable>
                  )}

                  {/* Submit Button */}
                  <Button
                    mode="contained"
                    onPress={handleSubmit}
                    loading={isLoading}
                    disabled={isLoading}
                    style={[styles.submitButton, { backgroundColor: branding.primaryColor }]}
                    contentStyle={styles.submitButtonContent}
                    labelStyle={styles.submitButtonLabel}
                  >
                    {isLoading ? (
                      <ActivityIndicator color="white" />
                    ) : (
                      isLogin ? 'Sign In' : 'Create Account'
                    )}
                  </Button>

                  {/* Forgot Password */}
                  {isLogin && (
                    <Pressable
                      onPress={() => {
                        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                        Alert.alert('Forgot Password', 'Password reset feature coming soon!');
                      }}
                      style={styles.forgotButton}
                    >
                      <Text style={[styles.forgotText, { color: branding.primaryColor }]}>
                        Forgot Password?
                      </Text>
                    </Pressable>
                  )}
                </View>

                {/* Social Login */}
                <View style={styles.socialSection}>
                  <View style={styles.dividerContainer}>
                    <Divider style={styles.divider} />
                    <Text style={styles.dividerText}>or continue with</Text>
                    <Divider style={styles.divider} />
                  </View>

                  <View style={styles.socialButtons}>
                    <Pressable
                      onPress={() => handleSocialLogin('Google')}
                      style={styles.socialButton}
                    >
                      <Surface style={styles.socialSurface} elevation={2}>
                        <Text style={styles.socialIcon}>G</Text>
                      </Surface>
                    </Pressable>
                    
                    <Pressable
                      onPress={() => handleSocialLogin('Apple')}
                      style={styles.socialButton}
                    >
                      <Surface style={styles.socialSurface} elevation={2}>
                        <Text style={styles.socialIcon}>🍎</Text>
                      </Surface>
                    </Pressable>
                    
                    <Pressable
                      onPress={() => handleSocialLogin('Microsoft')}
                      style={styles.socialButton}
                    >
                      <Surface style={styles.socialSurface} elevation={2}>
                        <Text style={styles.socialIcon}>Ⓜ</Text>
                      </Surface>
                    </Pressable>
                  </View>
                </View>

                {/* Quick Start */}
                {!isLogin && (
                  <View style={styles.quickStart}>
                    <Text style={styles.quickStartText}>
                      Want to explore first?
                    </Text>
                    <Pressable
                      onPress={() => {
                        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                        navigation.navigate('AgentOnboarding');
                      }}
                      style={styles.quickStartButton}
                    >
                      <Text style={[styles.quickStartButtonText, { color: branding.primaryColor }]}>
                        Start Demo →
                      </Text>
                    </Pressable>
                  </View>
                )}
              </Surface>
            </BlurView>
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  backgroundGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  backgroundCircle: {
    position: 'absolute',
    borderRadius: 200,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  circle1: {
    width: 300,
    height: 300,
    top: -100,
    right: -100,
  },
  circle2: {
    width: 200,
    height: 200,
    bottom: -50,
    left: -50,
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 40,
  },
  logoSection: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    overflow: 'hidden',
    marginBottom: 20,
  },
  logoGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoEmoji: {
    fontSize: 50,
  },
  appName: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  tagline: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  formContainer: {
    flex: 1,
  },
  blurContainer: {
    borderRadius: 24,
    overflow: 'hidden',
  },
  formCard: {
    borderRadius: 24,
    padding: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
  },
  modeToggle: {
    flexDirection: 'row',
    backgroundColor: '#F7FAFC',
    borderRadius: 12,
    padding: 4,
    marginBottom: 24,
  },
  modeButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
  },
  modeButtonActive: {
    backgroundColor: 'white',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  modeButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#64748B',
  },
  modeButtonTextActive: {
    color: '#2D3748',
    fontWeight: '600',
  },
  form: {
    marginBottom: 24,
  },
  inputContainer: {
    marginBottom: 16,
  },
  input: {
    backgroundColor: 'transparent',
  },
  biometricButton: {
    marginBottom: 16,
  },
  biometricSurface: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 12,
    backgroundColor: 'white',
  },
  biometricText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '500',
    color: '#2D3748',
  },
  submitButton: {
    borderRadius: 16,
    marginBottom: 16,
  },
  submitButtonContent: {
    paddingVertical: 12,
  },
  submitButtonLabel: {
    fontSize: 18,
    fontWeight: '600',
  },
  forgotButton: {
    alignSelf: 'center',
    padding: 8,
  },
  forgotText: {
    fontSize: 16,
    fontWeight: '500',
  },
  socialSection: {
    marginBottom: 16,
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: '#E2E8F0',
  },
  dividerText: {
    paddingHorizontal: 16,
    fontSize: 14,
    color: '#64748B',
  },
  socialButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
  },
  socialButton: {
    flex: 1,
    maxWidth: 80,
  },
  socialSurface: {
    width: '100%',
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'white',
  },
  socialIcon: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  quickStart: {
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  quickStartText: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 8,
  },
  quickStartButton: {
    padding: 8,
  },
  quickStartButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});