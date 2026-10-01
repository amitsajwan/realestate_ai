import React from 'react'
import Link from 'next/link'
import type { MarketingConfig } from '@/lib/marketing/config'
import { FOOTER, NAV } from '@/lib/marketing/strings'
import ContactBlock from './ContactBlock'
import { siteLinks, type SiteLink } from './siteLinks'

const link = 'flex min-h-[44px] items-center text-slate-800 underline decoration-slate-300 underline-offset-4 hover:decoration-slate-800'

function Column({ title, links }: { title: string; links: SiteLink[] }) {
  return (
    <div>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-600">{title}</h2>
      <ul className="mt-1 list-none p-0">
        {links.map((l) => (
          <li key={l.href}>
            {l.external ? (
              <a href={l.href} target="_blank" rel="noopener noreferrer" className={link}>{l.label}<span className="sr-only"> (opens in a new tab)</span></a>
            ) : (
              <Link href={l.href} className={link}>{l.label}</Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Cream footer: name and tagline with the phone-free contact block, then For agents / Explore / Legal link columns. */
export default function SiteFooter({ cfg }: { cfg: MarketingConfig }) {
  const s = siteLinks()
  return (
    <footer data-print="hide" className="border-t border-[#ead9ae] bg-[#fbf6ea] px-4 py-10 text-sm">
      <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-[1.3fr_2fr]">
        <div>
          <p className="text-base font-bold text-slate-900">{cfg.businessName}</p>
          <p className="mt-1 text-slate-700">{FOOTER.tagline}</p>
          <div className="mt-5"><ContactBlock tone="light" /></div>
        </div>
        <nav aria-label={NAV.footerLabel} className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3">
          <Column title="For agents" links={s.footerAgents} />
          <Column title="Explore" links={s.footerExplore} />
          <Column title="Legal" links={NAV.legal} />
        </nav>
      </div>
      <p className="mx-auto mt-8 max-w-5xl text-slate-600">&copy; {new Date().getFullYear()} {cfg.businessName}</p>
    </footer>
  )
}
