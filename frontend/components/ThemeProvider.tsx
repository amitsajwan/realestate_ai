'use client'

import React, { useEffect, useRef } from 'react'
import { initializeBrandTheme } from '@/lib/theme'

interface ThemeProviderProps {
  children: React.ReactNode
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
  const initialized = useRef(false)

  useEffect(() => {
    // Prevent multiple initializations
    if (initialized.current) {
      return
    }

    // Initialize theme on app startup
    try {
      console.info('[ThemeProvider] Initializing brand theme...');
      initializeBrandTheme();
      initialized.current = true
    } catch (error) {
      console.error('[ThemeProvider] Theme initialization failed:', error);
      // Don't throw - let the app continue without theme
    }
  }, [])

  return <>{children}</>
}