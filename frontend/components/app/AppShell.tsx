'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import React, { useEffect, useState } from 'react'
import { isFixtureMode } from '@/lib/app/client'
import { t } from '@/lib/app/strings'

const TABS = [
  { href: '/studio', label: 'home', icon: 'M3 11l9-8 9 8v9a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1z' },
  { href: '/studio/listings', label: 'listings', icon: 'M4 6h16M4 12h16M4 18h16' },
  { href: '/studio/interest', label: 'interest', icon: 'M21 11.5a8.4 8.4 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.4 8.4 0 01-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.4 8.4 0 013.8-.9h.5a8.5 8.5 0 018 8v.5z' },
  { href: '/studio/newsroom', label: 'newsroom', icon: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h11a2 2 0 012 2v3h3v9a2 2 0 01-2 2zM7 8h7M7 12h7M7 16h4' },
  { href: '/studio/content', label: 'content', icon: 'M4 5h16v14H4zM4 15l4-4 4 4 3-3 5 5M9 9h.01' },
  { href: '/studio/leads', label: 'leads', icon: 'M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 014-4h2a4 4 0 014 4v2zM12 7a3 3 0 11-6 0 3 3 0 016 0z' },
] as const

export function FixtureBanner() {
  const [on, setOn] = useState(false)
  useEffect(() => setOn(isFixtureMode()), [])
  if (!on) return null
  return <div className="bg-amber-100 px-3 py-1 text-center text-xs font-medium text-amber-900">{t('fixtureBanner')}</div>
}

/**
 * Full-screen phone shell. The root layout renders the legacy Navigation, so the shell is a fixed overlay
 * (z-50) that owns the whole viewport: scrollable content + bottom tab bar.
 */
export function AppShell({ children, hideTabs = false }: { children: React.ReactNode; hideTabs?: boolean }) {
  const path = usePathname() || ''
  const active = (href: string) => (href === '/studio' ? path === '/studio' : path.startsWith(href))
  return (
    <div data-surface="v2" className="fixed inset-0 z-50 flex flex-col bg-gray-50 text-gray-900">
      <FixtureBanner />
      {/* pb-28 leaves room for the tab bar; without tabs a sticky action bar must sit at the very bottom */}
      <main className={`mx-auto w-full max-w-md flex-1 overflow-y-auto px-4 pt-4 ${hideTabs ? 'pb-0' : 'pb-28'}`}>{children}</main>
      {!hideTabs && (
        <nav
          aria-label="Main"
          className="fixed inset-x-0 bottom-0 border-t border-gray-200 bg-white"
          style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
        >
          <ul className="mx-auto flex max-w-md">
            {TABS.map((tab) => (
              <li key={tab.href} className="flex-1">
                <Link
                  href={tab.href}
                  aria-current={active(tab.href) ? 'page' : undefined}
                  className={`flex min-h-[60px] flex-col items-center justify-center gap-1 text-xs font-semibold ${active(tab.href) ? 'text-blue-700' : 'text-gray-500'}`}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    <path d={tab.icon} />
                  </svg>
                  {t(tab.label)}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </div>
  )
}
