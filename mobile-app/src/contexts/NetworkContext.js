import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { Alert } from 'react-native';
import config from '../config/config';

const NetworkContext = createContext();

export const useNetwork = () => {
  const context = useContext(NetworkContext);
  if (!context) {
    throw new Error('useNetwork must be used within a NetworkProvider');
  }
  return context;
};

export const NetworkProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(true);
  const [isServerReachable, setIsServerReachable] = useState(true);
  const [lastChecked, setLastChecked] = useState(null);

  // Check network connectivity and server availability
  const checkConnection = async (showAlert = false) => {
    try {
      setLastChecked(new Date());
      const response = await axios.get(`${config.apiUrl}/health`, { timeout: 5000 });
      setIsConnected(true);
      setIsServerReachable(response.status === 200);
      return true;
    } catch (error) {
      const isNetworkError = !error.response;
      setIsConnected(!isNetworkError);
      setIsServerReachable(false);
      
      if (showAlert) {
        Alert.alert(
          'Connection Issue',
          isNetworkError
            ? 'Unable to connect to the internet. Please check your connection.'
            : 'Server is unreachable. Please try again later.',
          [{ text: 'OK' }]
        );
      }
      return false;
    }
  };

  // Retry a failed request
  const retryRequest = async (requestFn, maxRetries = 3) => {
    let retries = 0;
    while (retries < maxRetries) {
      try {
        return await requestFn();
      } catch (error) {
        retries++;
        if (retries >= maxRetries) {
          throw error;
        }
        // Wait before retrying (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retries)));
        // Check connection before retry
        await checkConnection(false);
      }
    }
  };

  useEffect(() => {
    // Initial connection check
    checkConnection(false);

    // Set up periodic connection check
    const intervalId = setInterval(() => checkConnection(false), 30000); // Check every 30 seconds
    
    return () => clearInterval(intervalId);
  }, []);

  const value = {
    isConnected,
    isServerReachable,
    lastChecked,
    checkConnection,
    retryRequest,
  };

  return (
    <NetworkContext.Provider value={value}>
      {children}
    </NetworkContext.Provider>
  );
};