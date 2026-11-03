import type { Metadata } from 'next'
import { ThemeProvider } from 'next-themes'
import { Inter } from 'next/font/google'
import React from 'react'
// The stylesheets the site's root layout gave Studio's screens before Studio became its own app (2026-11-03), in the same
// order, so the screens look as they did. Studio can trim them now that it owns them.
import '../styles/agent-website.css'
import '../styles/mobile-first.css'
import '../styles/mobile-forms.css'
import './globals.css'
import '../styles/design-tokens.css'
import '../styles/typography.css'
import '../styles/colors.css'
import '../styles/spacing.css'
import '../styles/components.css'
import '../styles/mobile.css'
import { BRAND_NAME, DEFAULT_DESCRIPTION, LOGO, NAVY } from '@shared/brand'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  applicationName: BRAND_NAME,
  description: DEFAULT_DESCRIPTION,
  // the icons and the manifest are the site's files on the same address
  icons: {
    icon: [
      { url: LOGO.icon32, sizes: '32x32', type: 'image/png' },
      { url: LOGO.icon192, sizes: '192x192', type: 'image/png' },
      { url: LOGO.mark, type: 'image/svg+xml' },
    ],
    apple: [{ url: LOGO.appleTouch, sizes: '180x180', type: 'image/png' }],
  },
  manifest: '/manifest.webmanifest',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: NAVY,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <a href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
            Skip to main content
          </a>
          <main id="main-content" className="min-h-screen bg-gray-50 dark:bg-gray-900">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  )
}
