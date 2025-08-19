import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface BrandingColors {
  primary: string;
  secondary: string;
  accent: string;
  text: string;
  background: string;
}

export interface BrandingAssets {
  logo_url?: string;
  favicon_url?: string;
  company_name?: string;
  company_description?: string;
  tagline?: string;
}

export interface BrandingConfig {
  colors: BrandingColors;
  assets: BrandingAssets;
}

interface BrandingContextType {
  branding: BrandingConfig;
  updateBranding: (newBranding: Partial<BrandingConfig>) => void;
  updateColors: (colors: Partial<BrandingColors>) => void;
  updateAssets: (assets: Partial<BrandingAssets>) => void;
  resetToDefault: () => void;
  applyBrandingToDOM: () => void;
}

const defaultBranding: BrandingConfig = {
  colors: {
    primary: '#2563eb',    // Blue
    secondary: '#7c3aed',  // Purple
    accent: '#f59e0b',     // Amber
    text: '#1f2937',       // Dark gray
    background: '#ffffff'   // White
  },
  assets: {
    company_name: 'World Glass Gen AI Property CRM',
    tagline: 'Your Trusted Real Estate Partner'
  }
};

const BrandingContext = createContext<BrandingContextType | undefined>(undefined);

export const useBranding = () => {
  const context = useContext(BrandingContext);
  if (!context) {
    throw new Error('useBranding must be used within a BrandingProvider');
  }
  return context;
};

interface BrandingProviderProps {
  children: ReactNode;
  initialBranding?: Partial<BrandingConfig>;
}

export const BrandingProvider: React.FC<BrandingProviderProps> = ({ 
  children, 
  initialBranding 
}) => {
  const [branding, setBranding] = useState<BrandingConfig>({
    ...defaultBranding,
    ...initialBranding
  });

  // Apply branding to DOM CSS variables
  const applyBrandingToDOM = () => {
    const root = document.documentElement;
    root.style.setProperty('--primary-color', branding.colors.primary);
    root.style.setProperty('--secondary-color', branding.colors.secondary);
    root.style.setProperty('--accent-color', branding.colors.accent);
    root.style.setProperty('--text-color', branding.colors.text);
    root.style.setProperty('--background-color', branding.colors.background);
    
    // Set additional CSS variables for gradients and shadows
    root.style.setProperty('--primary-gradient', `linear-gradient(135deg, ${branding.colors.primary}, ${branding.colors.secondary})`);
    root.style.setProperty('--accent-gradient', `linear-gradient(135deg, ${branding.colors.accent}, ${branding.colors.primary})`);
    root.style.setProperty('--primary-shadow', `0 4px 14px 0 ${branding.colors.primary}20`);
    root.style.setProperty('--secondary-shadow', `0 4px 14px 0 ${branding.colors.secondary}20`);
  };

  // Update entire branding configuration
  const updateBranding = (newBranding: Partial<BrandingConfig>) => {
    setBranding(prev => ({
      ...prev,
      ...newBranding,
      colors: {
        ...prev.colors,
        ...(newBranding.colors || {})
      },
      assets: {
        ...prev.assets,
        ...(newBranding.assets || {})
      }
    }));
  };

  // Update only colors
  const updateColors = (colors: Partial<BrandingColors>) => {
    setBranding(prev => ({
      ...prev,
      colors: {
        ...prev.colors,
        ...colors
      }
    }));
  };

  // Update only assets
  const updateAssets = (assets: Partial<BrandingAssets>) => {
    setBranding(prev => ({
      ...prev,
      assets: {
        ...prev.assets,
        ...assets
      }
    }));
  };

  // Reset to default branding
  const resetToDefault = () => {
    setBranding(defaultBranding);
  };

  // Apply branding whenever it changes
  useEffect(() => {
    applyBrandingToDOM();
  }, [branding]);

  // Apply initial branding on mount
  useEffect(() => {
    applyBrandingToDOM();
  }, []);

  const value: BrandingContextType = {
    branding,
    updateBranding,
    updateColors,
    updateAssets,
    resetToDefault,
    applyBrandingToDOM
  };

  return (
    <BrandingContext.Provider value={value}>
      {children}
    </BrandingContext.Provider>
  );
};