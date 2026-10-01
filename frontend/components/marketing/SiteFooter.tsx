import React from 'react'
import Link from 'next/link'
import type { MarketingConfig } from '@/lib/marketing/config'
import { FOOTER, NAV, PATHS } from '@/lib/marketing/strings'
import ContactLines from './ContactLines'

export default function SiteFooter({ cfg }: { cfg: MarketingConfig }) {
  const link = 'flex min-h-[44px] items-center text-slate-800 underline decoration-slate-300 underline-offset-4 hover:decoration-slate-800'
  return (
    <footer className="border-t border-[#ead9ae] bg-[#fbf6ea] px-4 py-10 text-sm">
      <div className="mx-auto grid max-w-5xl gap-8 sm:grid-cols-2">
        <div>
          <p className="text-base font-bold text-slate-900">{cfg.businessName}</p>
          <p className="mt-1 text-slate-700">{FOOTER.tagline}</p>
          <h2 className="mt-5 text-sm font-semibold uppercase tracking-wide text-slate-600">{FOOTER.contactHeading}</h2>
          <div className="mt-2"><ContactLines cfg={cfg} /></div>
        </div>
        <nav aria-label={NAV.footerLabel}>
          <ul className="grid grid-cols-2 gap-x-4">
            <li><Link href={PATHS.invite} className={link}>{NAV.requestInvite}</Link></li>
            <li><Link href={PATHS.signIn} className={link}>{NAV.signIn}</Link></li>
            <li><Link href="/insights" className={link}>Insights</Link></li>
            <li><Link href="/localities" className={link}>Localities</Link></li>
            {NAV.legal.map((l) => (
              <li key={l.href}><Link href={l.href} className={link}>{l.label}</Link></li>
            ))}
          </ul>
        </nav>
      </div>
      <p className="mx-auto mt-8 max-w-5xl text-slate-600">&copy; {new Date().getFullYear()} {cfg.businessName}</p>
    </footer>
  )
}
