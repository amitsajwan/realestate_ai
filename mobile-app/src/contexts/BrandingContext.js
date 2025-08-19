import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BrandingContext = createContext();

export const useBranding = () => {
  const context = useContext(BrandingContext);
  if (!context) {
    throw new Error('useBranding must be used within a BrandingProvider');
  }
  return context;
};

export const BrandingProvider = ({ children }) => {
  const [branding, setBranding] = useState({
    logo: null,
    primaryColor: '#2E86AB',
    secondaryColor: '#A23B72',
    accentColor: '#F18F01',
    backgroundColor: '#FFFFFF',
    textColor: '#2D3748',
    agentName: '',
    companyName: '',
    tagline: '',
    tags: [],
    theme: 'light', // 'light' | 'dark'
  });

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadBrandingFromStorage();
  }, []);

  const loadBrandingFromStorage = async () => {
    try {
      const storedBranding = await AsyncStorage.getItem('agentBranding');
      if (storedBranding) {
        setBranding(JSON.parse(storedBranding));
      }
    } catch (error) {
      console.error('Error loading branding:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateBranding = async (newBranding) => {
    try {
      const updatedBranding = { ...branding, ...newBranding };
      setBranding(updatedBranding);
      await AsyncStorage.setItem('agentBranding', JSON.stringify(updatedBranding));
    } catch (error) {
      console.error('Error saving branding:', error);
    }
  };

  const resetBranding = async () => {
    try {
      await AsyncStorage.removeItem('agentBranding');
      setBranding({
        logo: null,
        primaryColor: '#2E86AB',
        secondaryColor: '#A23B72',
        accentColor: '#F18F01',
        backgroundColor: '#FFFFFF',
        textColor: '#2D3748',
        agentName: '',
        companyName: '',
        tagline: '',
        tags: [],
        theme: 'light',
      });
    } catch (error) {
      console.error('Error resetting branding:', error);
    }
  };

  const getThemeColors = () => {
    if (branding.theme === 'dark') {
      return {
        ...branding,
        backgroundColor: '#1A202C',
        textColor: '#F7FAFC',
        cardBackground: '#2D3748',
        borderColor: '#4A5568',
      };
    }
    return {
      ...branding,
      backgroundColor: '#FFFFFF',
      textColor: '#2D3748',
      cardBackground: '#FFFFFF',
      borderColor: '#E2E8F0',
    };
  };

  const generateColorPalette = (primaryColor) => {
    // Generate complementary colors based on primary color
    // This is a simplified version - in production, you'd use a proper color theory library
    const hsl = hexToHsl(primaryColor);
    return {
      primaryColor,
      secondaryColor: hslToHex((hsl.h + 120) % 360, hsl.s, hsl.l),
      accentColor: hslToHex((hsl.h + 240) % 360, hsl.s, hsl.l),
    };
  };

  const value = {
    branding: getThemeColors(),
    updateBranding,
    resetBranding,
    generateColorPalette,
    isLoading,
  };

  return (
    <BrandingContext.Provider value={value}>
      {children}
    </BrandingContext.Provider>
  );
};

// Helper functions for color manipulation
function hexToHsl(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;

  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }

  return { h: h * 360, s: s * 100, l: l * 100 };
}

function hslToHex(h, s, l) {
  h /= 360;
  s /= 100;
  l /= 100;

  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs((h * 6) % 2 - 1));
  const m = l - c / 2;
  let r = 0, g = 0, b = 0;

  if (0 <= h && h < 1/6) {
    r = c; g = x; b = 0;
  } else if (1/6 <= h && h < 1/3) {
    r = x; g = c; b = 0;
  } else if (1/3 <= h && h < 1/2) {
    r = 0; g = c; b = x;
  } else if (1/2 <= h && h < 2/3) {
    r = 0; g = x; b = c;
  } else if (2/3 <= h && h < 5/6) {
    r = x; g = 0; b = c;
  } else if (5/6 <= h && h < 1) {
    r = c; g = 0; b = x;
  }

  r = Math.round((r + m) * 255);
  g = Math.round((g + m) * 255);
  b = Math.round((b + m) * 255);

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}