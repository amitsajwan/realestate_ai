import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Card,
  Divider,
  HelperText,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useAuth } from '../contexts/AuthContext';
import { useBranding } from '../contexts/BrandingContext';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);

  const { login, register } = useAuth();
  const { branding } = useBranding();

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
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    
    try {
      let result;
      if (isLogin) {
        result = await login(email, password);
      } else {
        result = await register({ email, password });
      }

      if (result.success) {
        if (result.user?.onboardingCompleted) {
          navigation.replace('Main');
        } else {
          navigation.replace('AgentOnboarding');
        }
      } else {
        Alert.alert('Error', result.error);
      }
    } catch (error) {
      Alert.alert('Error', 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setErrors({});
    setEmail('');
    setPassword('');
  };

  return (
    <LinearGradient
      colors={[branding.primaryColor, branding.secondaryColor]}
      style={styles.container}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoid}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <Animatable.View
            animation="fadeInDown"
            duration={1000}
            style={styles.header}
          >
            <View style={styles.logo}>
              <Text style={styles.logoText}>🏠</Text>
            </View>
            <Text style={styles.appName}>PropertyAI</Text>
            <Text style={styles.welcomeText}>
              {isLogin ? 'Welcome back!' : 'Join the future of real estate'}
            </Text>
          </Animatable.View>

          <Animatable.View
            animation="fadeInUp"
            duration={1000}
            delay={300}
          >
            <Card style={styles.formCard}>
              <View style={styles.formContent}>
                <Text style={styles.formTitle}>
                  {isLogin ? 'Sign In' : 'Create Account'}
                </Text>
                
                <View style={styles.form}>
                  <TextInput
                    label="Email Address"
                    value={email}
                    onChangeText={setEmail}
                    mode="outlined"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    style={styles.input}
                    error={!!errors.email}
                    theme={{ colors: { primary: branding.primaryColor } }}
                  />
                  <HelperText type="error" visible={!!errors.email}>
                    {errors.email}
                  </HelperText>

                  <TextInput
                    label="Password"
                    value={password}
                    onChangeText={setPassword}
                    mode="outlined"
                    secureTextEntry={!showPassword}
                    style={styles.input}
                    error={!!errors.password}
                    theme={{ colors: { primary: branding.primaryColor } }}
                    right={
                      <TextInput.Icon
                        icon={showPassword ? 'eye-off' : 'eye'}
                        onPress={() => setShowPassword(!showPassword)}
                      />
                    }
                  />
                  <HelperText type="error" visible={!!errors.password}>
                    {errors.password}
                  </HelperText>

                  <Button
                    mode="contained"
                    onPress={handleSubmit}
                    loading={isLoading}
                    disabled={isLoading}
                    style={[styles.submitButton, { backgroundColor: branding.primaryColor }]}
                    contentStyle={styles.submitButtonContent}
                  >
                    {isLogin ? 'Sign In' : 'Create Account'}
                  </Button>

                  {isLogin && (
                    <Button
                      mode="text"
                      onPress={() => Alert.alert('Forgot Password', 'Password reset feature coming soon!')}
                      style={styles.forgotButton}
                      textColor={branding.primaryColor}
                    >
                      Forgot Password?
                    </Button>
                  )}
                </View>

                <Divider style={styles.divider} />

                <View style={styles.switchModeContainer}>
                  <Text style={styles.switchModeText}>
                    {isLogin ? "Don't have an account?" : "Already have an account?"}
                  </Text>
                  <Button
                    mode="text"
                    onPress={toggleMode}
                    textColor={branding.primaryColor}
                    style={styles.switchModeButton}
                  >
                    {isLogin ? 'Sign Up' : 'Sign In'}
                  </Button>
                </View>

                {!isLogin && (
                  <Button
                    mode="outlined"
                    onPress={() => navigation.navigate('AgentOnboarding')}
                    style={styles.skipButton}
                    textColor={branding.primaryColor}
                  >
                    Start Agent Onboarding
                  </Button>
                )}
              </View>
            </Card>
          </Animatable.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 40,
  },
  appName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  welcomeText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
  },
  formCard: {
    borderRadius: 20,
    elevation: 8,
  },
  formContent: {
    padding: 24,
  },
  formTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 24,
    color: '#2D3748',
  },
  form: {
    marginBottom: 20,
  },
  input: {
    marginBottom: 4,
  },
  submitButton: {
    marginTop: 16,
    borderRadius: 12,
  },
  submitButtonContent: {
    paddingVertical: 8,
  },
  forgotButton: {
    marginTop: 8,
    alignSelf: 'center',
  },
  divider: {
    marginVertical: 20,
  },
  switchModeContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  switchModeText: {
    color: '#64748B',
  },
  switchModeButton: {
    marginLeft: 8,
  },
  skipButton: {
    borderRadius: 12,
  },
});