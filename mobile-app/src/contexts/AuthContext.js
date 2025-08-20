import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
// Removed expo-secure-store due to config plugin error
import { Alert } from 'react-native';
import config from '../config/config';
import apiService, { setAuthToken } from '../services/apiService';
import { useNetwork } from './NetworkContext';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};



export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const { isConnected, isServerReachable } = useNetwork();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = await SecureStore.getItemAsync(config.authTokenKey);
      const userData = await AsyncStorage.getItem(config.userDataKey);
      
      if (token && userData) {
        setUser(JSON.parse(userData));
        setIsAuthenticated(true);
        // Set auth token for API requests
        setAuthToken(token);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      setIsLoading(true);
      
      const result = await apiService.auth.login(email, password);
      
      if (result.success) {
        const { token, user: userData } = result.data;
        
        // Store token securely
        await SecureStore.setItemAsync(config.authTokenKey, token);
        await AsyncStorage.setItem(config.userDataKey, JSON.stringify(userData));
        
        // Set auth token for API requests
        setAuthToken(token);
        
        setUser(userData);
        setIsAuthenticated(true);
        
        return { success: true, user: userData };
      } else {
        return { 
          success: false, 
          error: result.message || 'Login failed' 
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: 'Login failed. Please try again.' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setIsLoading(true);
      
      const result = await apiService.auth.register(userData);
      
      if (result.success) {
        const { token, user: newUser } = result.data;
        
        // Store token securely
        await SecureStore.setItemAsync(config.authTokenKey, token);
        await AsyncStorage.setItem(config.userDataKey, JSON.stringify(newUser));
        
        // Set auth token for API requests
        setAuthToken(token);
        
        setUser(newUser);
        setIsAuthenticated(true);
        
        return { success: true, user: newUser };
      } else {
        return { 
          success: false, 
          error: result.message || 'Registration failed' 
        };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        error: 'Registration failed. Please try again.' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Clear stored data
      await SecureStore.deleteItemAsync(config.authTokenKey);
      await AsyncStorage.removeItem(config.userDataKey);
      
      // Clear auth token
      setAuthToken(null);
      
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const result = await apiService.auth.updateProfile(profileData);
      
      if (result.success) {
        const updatedUser = result.data;
        
        await AsyncStorage.setItem(config.userDataKey, JSON.stringify(updatedUser));
        setUser(updatedUser);
        
        return { success: true, user: updatedUser };
      } else {
        return { 
          success: false, 
          error: result.message || 'Profile update failed' 
        };
      }
    } catch (error) {
      console.error('Profile update error:', error);
      return { 
        success: false, 
        error: 'Profile update failed. Please try again.' 
      };
    }
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    isConnected,
    isServerReachable,
    login,
    register,
    logout,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};