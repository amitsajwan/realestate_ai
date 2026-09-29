import React from 'react'
import Link from 'next/link'
import { NAV, PATHS } from '@/lib/marketing/strings'

export default function SiteHeader({ businessName, showInviteCta = true }: { businessName: string; showInviteCta?: boolean }) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-4 py-1.5">
        <Link href={PATHS.home} className="flex min-h-[44px] items-center whitespace-nowrap text-base font-bold text-slate-900 no-underline sm:text-lg">
          {businessName}
        </Link>
        <nav aria-label={NAV.primaryLabel} className="flex items-center gap-1 text-sm">
          <Link href={PATHS.signIn} className="flex min-h-[44px] items-center whitespace-nowrap px-2 font-medium text-slate-700 no-underline hover:text-slate-900 sm:px-3">
            {NAV.signIn}
          </Link>
          {showInviteCta && (
            <Link href={PATHS.invite}
              className="flex min-h-[44px] items-center whitespace-nowrap rounded-lg bg-blue-700 px-3 font-semibold text-white no-underline hover:bg-blue-800 sm:px-4">
              {NAV.requestInvite}
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
