import React from 'react'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ThemeProvider } from 'next-themes'
import { SkipLink } from '@/lib/accessibility'
import Navigation from '@/components/Navigation'
import BreadcrumbNavigation from '@/components/BreadcrumbNavigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'PropertyAI - AI-Powered Real Estate Platform',
  description: 'Modern real estate platform with AI-powered property management and lead generation',
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
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <BreadcrumbNavigation />
                {children}
              </div>
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
