import React from 'react'
import Link from 'next/link'
import { NAV, PATHS } from '@/lib/marketing/strings'
import { LOGO } from '@/lib/brand'
import { siteLinks, type Audience, type SiteLink } from './siteLinks'

function NavLink({ l, className }: { l: SiteLink; className: string }) {
  return l.external ? (
    <a href={l.href} target="_blank" rel="noopener noreferrer" className={className}>
      {l.label}<span className="sr-only"> (opens in a new tab)</span>
    </a>
  ) : (
    <Link href={l.href} className={className}>{l.label}</Link>
  )
}

/** Which button the header shows: the buyer's 'Tell us what you need', the agent's 'Request an invite', or none (the invite page itself). */
export type HeaderCta = Audience | 'none'

const button = 'flex min-h-[44px] items-center whitespace-nowrap rounded-lg bg-[#f0b440] px-3 font-bold text-[#0f2340] no-underline hover:bg-[#f5c75e] sm:px-4'

/** Navy header: mark + name, the main links on wide screens, a Menu disclosure on phones (no JavaScript needed), and one gold button
 *  chosen by the page's audience: buyer pages (the default) ask what the visitor needs, agent pages offer the invite. */
export default function SiteHeader({ businessName, cta = 'buyer' }: { businessName: string; cta?: HeaderCta }) {
  const s = siteLinks()
  const wide = 'hidden min-h-[44px] items-center whitespace-nowrap px-2 font-medium text-white/90 no-underline hover:text-white lg:flex xl:px-3'
  const item = 'flex min-h-[48px] items-center border-b border-white/10 px-1 font-medium text-white no-underline last:border-b-0'
  return (
    <header data-print="hide" className="sticky top-0 z-30 border-b border-[#1d3a63] bg-[#0f2340] text-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-4 py-1.5">
        <Link href={PATHS.home} className="flex min-h-[44px] items-center gap-2 whitespace-nowrap text-base font-bold text-white no-underline sm:text-lg">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LOGO.mark} alt="" width={32} height={32} className="h-8 w-8" />
          {businessName}
        </Link>
        <nav aria-label={NAV.primaryLabel} className="flex items-center gap-1 text-sm">
          {s.headerWide[cta === 'agent' ? 'agent' : 'buyer'].map((l) => <NavLink key={l.href} l={l} className={wide} />)}
          <NavLink l={s.signIn} className={wide} />
          {cta === 'buyer' && (
            // the short words on phones are the start of the full name, so voice control users can say what they see
            <a href={s.need.href} aria-label={s.need.label} data-testid="header-cta" className={button}>
              <span className="sm:hidden">Tell us</span><span className="hidden sm:inline">{s.need.label}</span>
            </a>
          )}
          {cta === 'agent' && (
            <Link href={s.invite.href} data-testid="header-cta" className={button}>{NAV.requestInvite}</Link>
          )}
          <details className="group relative lg:hidden">
            <summary className="flex min-h-[44px] cursor-pointer list-none items-center gap-1.5 rounded-lg px-2 font-semibold text-white [&::-webkit-details-marker]:hidden">
              <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M4 7h16M4 12h16M4 17h16" className="group-open:hidden" />
                <path d="M6 6l12 12M18 6L6 18" className="hidden group-open:block" />
              </svg>
              Menu
            </summary>
            <div className="absolute right-0 top-full mt-2 w-64 rounded-2xl border border-white/15 bg-[#0f2340] p-3 shadow-2xl">
              <ul className="m-0 list-none p-0">
                {s.menu.map((l) => <li key={l.href}><NavLink l={l} className={item} /></li>)}
              </ul>
            </div>
          </details>
        </nav>
      </div>
    </header>
  )
}
