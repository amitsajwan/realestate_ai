import { ErrorBoundary } from '@/components/ErrorBoundary'
import Navigation from '@/components/Navigation'
import { SkipLink } from '@/lib/accessibility'
import type { Metadata } from 'next'
import { ThemeProvider } from 'next-themes'
import { Inter } from 'next/font/google'
import React from 'react'
import { Toaster } from 'react-hot-toast'
import '../styles/agent-website.css'
import '../styles/mobile-first.css'
import '../styles/mobile-forms.css'
import './globals.css'
// design system (was @import-ed inside globals.css; must come after Tailwind's rules, in this order)
import '../styles/design-tokens.css'
import '../styles/typography.css'
import '../styles/colors.css'
import '../styles/spacing.css'
import '../styles/components.css'
import '../styles/mobile.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'PropertyAI - AI-Powered Real Estate Platform',
  description: 'Modern real estate platform with AI-powered property management and lead generation',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <ErrorBoundary>
            <SkipLink href="#main-content">Skip to main content</SkipLink>
            <SkipLink href="#navigation">Skip to navigation</SkipLink>
            <Navigation />
            <main id="main-content" className="min-h-screen bg-gray-50 dark:bg-gray-900">
              {children}
            </main>
          </ErrorBoundary>
        </ThemeProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </body>
    </html>
  )
}
