/**
 * Application Configuration
 * 
 * This file centralizes all configuration settings for the mobile app.
 * Environment variables are loaded from Expo's Constants.manifest.extra
 * which gets values from app.config.js
 */

import Constants from 'expo-constants';

// Default values for development
const DEV_API_URL = 'http://127.0.0.1:8003';
const PROD_API_URL = 'https://api.propertyai.com'; // Replace with actual production URL

// Get environment variables from Expo config
const getEnvVars = () => {
  try {
    // For Expo SDK 48 and above
    return Constants.expoConfig?.extra || {};
  } catch (error) {
    console.warn('Error loading environment variables:', error);
    return {};
  }
};

const env = getEnvVars();

// Determine if we're in production
const isProduction = process.env.NODE_ENV === 'production';

const config = {
  // API Configuration
  apiUrl: isProduction ? PROD_API_URL : (env.API_URL || DEV_API_URL),
  
  // Authentication keys
  authTokenKey: 'authToken',
  userDataKey: 'userData',
  brandingKey: 'branding',
  
  // AI Services
  groqApiKey: env.GROQ_API_KEY || '',
  
  // App Information
  appVersion: Constants.expoConfig?.version || '1.0.0',
  buildNumber: Constants.expoConfig?.ios?.buildNumber || '1',
  
  // Feature Flags
  enablePushNotifications: false,
  enableOfflineMode: false,
  
  // Timeouts (in milliseconds)
  apiTimeout: 15000,
  
  // Default Branding
  defaultBranding: {
    primaryColor: '#2E86AB',
    secondaryColor: '#A23B72',
    accentColor: '#F18F01',
    backgroundColor: '#FFFFFF',
    textColor: '#2D3748',
  }
};

export default config;