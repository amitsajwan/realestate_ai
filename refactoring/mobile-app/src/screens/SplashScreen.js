import React, { useEffect } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { Text } from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useAuth } from '../contexts/AuthContext';
import { useBranding } from '../contexts/BrandingContext';

const { width, height } = Dimensions.get('window');

export default function SplashScreen({ navigation }) {
  const { isAuthenticated, isLoading } = useAuth();
  const { branding, isLoading: brandingLoading } = useBranding();

  useEffect(() => {
    if (!isLoading && !brandingLoading) {
      const timer = setTimeout(() => {
        if (isAuthenticated) {
          navigation.replace('Main');
        } else {
          navigation.replace('Onboarding');
        }
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [isLoading, brandingLoading, isAuthenticated, navigation]);

  return (
    <LinearGradient
      colors={[branding.primaryColor, branding.secondaryColor]}
      style={styles.container}
    >
      <View style={styles.content}>
        <Animatable.View
          animation="bounceIn"
          duration={1500}
          style={styles.logoContainer}
        >
          <View style={styles.logo}>
            <Text style={styles.logoText}>🏠</Text>
          </View>
          <Animatable.Text
            animation="fadeInUp"
            delay={800}
            style={styles.appName}
          >
            PropertyAI
          </Animatable.Text>
          <Animatable.Text
            animation="fadeInUp"
            delay={1000}
            style={styles.tagline}
          >
            World's First Gen AI Property Solution
          </Animatable.Text>
        </Animatable.View>

        <Animatable.View
          animation="fadeInUp"
          delay={1200}
          style={styles.loadingContainer}
        >
          <View style={styles.loadingBar}>
            <Animatable.View
              animation="slideInRight"
              duration={1000}
              style={styles.loadingFill}
            />
          </View>
          <Text style={styles.loadingText}>Initializing...</Text>
        </Animatable.View>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 80,
  },
  logo: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 32,
  },
  logoText: {
    fontSize: 60,
  },
  appName: {
    fontSize: 36,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 16,
    textAlign: 'center',
  },
  tagline: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  loadingContainer: {
    alignItems: 'center',
    position: 'absolute',
    bottom: 100,
    width: width * 0.8,
  },
  loadingBar: {
    width: '100%',
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: 16,
  },
  loadingFill: {
    height: '100%',
    width: '100%',
    backgroundColor: 'white',
    borderRadius: 2,
  },
  loadingText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 16,
  },
});