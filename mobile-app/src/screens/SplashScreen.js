import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Dimensions, Alert } from 'react-native';
import { Text, ActivityIndicator } from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useAuth } from '../contexts/AuthContext';
import { useBranding } from '../contexts/BrandingContext';
import { useNetwork } from '../contexts/NetworkContext';
import config from '../config/config';

const { width, height } = Dimensions.get('window');

export default function SplashScreen({ navigation }) {
  const { isAuthenticated, isLoading } = useAuth();
  const { branding, isLoading: brandingLoading } = useBranding();
  const { isConnected, isServerReachable, checkServerReachability } = useNetwork();
  const [loadingStatus, setLoadingStatus] = useState('Initializing...');
  const [retryCount, setRetryCount] = useState(0);
  const [showOfflineAlert, setShowOfflineAlert] = useState(false);

  // Check network and server status
  useEffect(() => {
    const checkConnection = async () => {
      setLoadingStatus('Checking connection...');
      await checkServerReachability();
    };
    
    checkConnection();
    
    // Set up periodic connection check
    const intervalId = setInterval(checkConnection, 5000); // Check every 5 seconds during splash
    
    return () => clearInterval(intervalId);
  }, []);

  // Handle navigation based on auth status
  useEffect(() => {
    if (!isLoading && !brandingLoading) {
      if (!isConnected) {
        setLoadingStatus('No internet connection');
        if (config.enableOfflineMode && !showOfflineAlert) {
          setShowOfflineAlert(true);
          Alert.alert(
            'Offline Mode',
            'No internet connection detected. Some features may be limited.',
            [
              { 
                text: 'Continue Offline', 
                onPress: () => {
                  if (isAuthenticated) {
                    navigation.replace('Main');
                  } else {
                    // Can't authenticate offline
                    navigation.replace('Onboarding');
                  }
                }
              },
              { 
                text: 'Retry', 
                onPress: () => {
                  setShowOfflineAlert(false);
                  setRetryCount(retryCount + 1);
                  checkServerReachability();
                }
              }
            ],
            { cancelable: false }
          );
        }
        return;
      }
      
      if (!isServerReachable && retryCount < 3) {
        setLoadingStatus('Connecting to server...');
        setRetryCount(retryCount + 1);
        return;
      }

      setLoadingStatus('Loading app...');
      const timer = setTimeout(() => {
        if (isAuthenticated) {
          navigation.replace('Main');
        } else {
          navigation.replace('Onboarding');
        }
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [isLoading, brandingLoading, isAuthenticated, isConnected, isServerReachable, navigation, retryCount]);

  return (
    <LinearGradient
      colors={[branding.colors?.primaryColor || config.defaultBranding.primaryColor, 
               branding.colors?.secondaryColor || config.defaultBranding.secondaryColor]}
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
          {(isLoading || brandingLoading || !isConnected || !isServerReachable) && (
            <ActivityIndicator 
              animating={true} 
              color="#fff" 
              size="large" 
              style={styles.activityIndicator} 
            />
          )}
          <Text style={styles.loadingText}>{loadingStatus}</Text>
          {!isConnected && (
            <Text style={styles.errorText}>No internet connection</Text>
          )}
          {isConnected && !isServerReachable && retryCount >= 3 && (
            <Text style={styles.errorText}>Server unreachable. Check your API URL.</Text>
          )}
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    elevation: 8,
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
  activityIndicator: {
    marginBottom: 16,
  },
  loadingText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 16,
  },
  errorText: {
    color: '#ffcccc',
    fontSize: 14,
    fontWeight: '500',
    marginTop: 8,
    textAlign: 'center',
  },
});