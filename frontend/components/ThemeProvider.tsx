'use client'

import React, { useEffect } from 'react'
import { initializeBrandTheme } from '@/lib/theme'

interface ThemeProviderProps {
  children: React.ReactNode
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
  useEffect(() => {
    // Initialize theme on app startup
    try {
      console.info('[ThemeProvider] Initializing brand theme...');
      initializeBrandTheme();
    } catch (error) {
      console.error('[ThemeProvider] Theme initialization failed:', error);
      // Don't throw - let the app continue without theme
    }
  }, [])

  return <>{children}</>
}