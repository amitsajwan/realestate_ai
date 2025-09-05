'use client'

import React, { useEffect } from 'react'
import { initializeBrandTheme } from '@/lib/theme'

interface ThemeProviderProps {
  children: React.ReactNode
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
  useEffect(() => {
    // Initialize theme on app startup
  console.info('[ThemeProvider] Initializing brand theme...');
    initializeBrandTheme();
  }, [])

  return <>{children}</>
}