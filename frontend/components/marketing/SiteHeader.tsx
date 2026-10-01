import React from 'react'
import Link from 'next/link'
import { NAV, PATHS } from '@/lib/marketing/strings'

export default function SiteHeader({ businessName, showInviteCta = true }: { businessName: string; showInviteCta?: boolean }) {
  return (
    <header className="sticky top-0 z-30 border-b border-[#1d3a63] bg-[#0f2340] text-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-4 py-1.5">
        <Link href={PATHS.home} className="flex min-h-[44px] items-center gap-2 whitespace-nowrap text-base font-bold text-white no-underline sm:text-lg">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/logo.png" alt="" width={32} height={32} className="h-8 w-8 rounded-full" />
          {businessName}
        </Link>
        <nav aria-label={NAV.primaryLabel} className="flex items-center gap-1 text-sm">
          <Link href={PATHS.signIn} className="flex min-h-[44px] items-center whitespace-nowrap px-2 font-medium text-white/90 no-underline hover:text-white sm:px-3">
            {NAV.signIn}
          </Link>
          {showInviteCta && (
            <Link href={PATHS.invite}
              className="flex min-h-[44px] items-center whitespace-nowrap rounded-lg bg-[#f0b440] px-3 font-bold text-[#0f2340] no-underline hover:bg-[#f5c75e] sm:px-4">
              {NAV.requestInvite}
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
