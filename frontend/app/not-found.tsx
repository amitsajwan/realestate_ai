import React from 'react'
import Link from 'next/link'
import MarketingShell from '@/components/marketing/MarketingShell'

export const metadata = { title: 'Page not found', robots: { index: false } }

const NEXT = [
  { href: '/projects', label: 'New projects in Pune', note: 'Every MahaRERA project, with its filed completion date' },
  { href: '/check', label: 'Check your project', note: 'Has your possession date moved? Search by name or RERA number' },
  { href: '/builders', label: 'Builders', note: 'Each builder’s record of finishing on time' },
  { href: '/localities', label: 'Area guides', note: 'Kharadi, Wagholi, Hinjawadi, Wakad, Baner and more' },
]

/** Where every broken or old link lands: the site's own header and footer, and the four places most visitors were going. */
export default function NotFound() {
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl px-4 py-12 sm:py-16">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#a87a1c]">Page not found</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">This page has moved or no longer exists</h1>
        <p className="mt-4 text-lg leading-relaxed text-slate-700">
          The link may be old, or the project may have been renamed. One of these will likely get you there:
        </p>
        <ul className="mt-6 grid list-none gap-3 p-0 sm:grid-cols-2">
          {NEXT.map((l) => (
            <li key={l.href}>
              <Link href={l.href} className="block h-full rounded-xl border border-slate-200 bg-white p-4 no-underline shadow-sm hover:border-[#0f2340]">
                <span className="block font-semibold text-[#0f2340]">{l.label} &rarr;</span>
                <span className="mt-1 block text-sm text-slate-600">{l.note}</span>
              </Link>
            </li>
          ))}
        </ul>
        <p className="mt-8">
          <Link href="/" className="inline-flex min-h-[48px] items-center rounded-xl bg-[#0f2340] px-6 font-bold text-white no-underline hover:bg-[#183a5d]">Go to the home page</Link>
        </p>
      </div>
    </MarketingShell>
  )
}
