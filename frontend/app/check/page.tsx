import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import CheckSearch from '@/components/site/CheckSearch'
import InstallApp from '@/components/site/InstallApp'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { searchRegister } from '@/lib/site/register'

/** The project check (docs/plan/project-check.md): one job, find your project and see what its possession date did on MahaRERA.
 *  The installed app opens here (app/manifest.ts). */
export const revalidate = 300

export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata(getMarketingConfig(), {
    title: 'Check your project on MahaRERA: possession date, delays, homes booked',
    description: 'Bought a flat in Pune or planning to? Search your project and see its possession date on MahaRERA, whether it moved later, and how many homes are booked. Free.',
    path: '/check',
  })
}

type Props = { searchParams?: Promise<{ q?: string | string[] }> }

const SHOWS: [string, string][] = [
  ['Possession date', 'the date the builder filed on MahaRERA now, and whether it moved since registration'],
  ['Homes booked', 'how many of the project’s homes are sold, as the builder reports them'],
  ['The builder’s record', 'how many of their other projects moved their date, and by how much'],
]

export default async function CheckPage({ searchParams }: Props) {
  const raw = (await searchParams)?.q
  const q = (Array.isArray(raw) ? raw[0] : raw ?? '').trim().slice(0, 80)
  const hits = q.length >= 2 ? await searchRegister(q, 12) : []
  return (
    <MarketingShell search={false}>
      <div className="bg-[#0f2340] px-4 pb-10 pt-8 text-white sm:pb-14 sm:pt-12">
        <div className="mx-auto max-w-xl">
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-300">Free · Pune · from MahaRERA</p>
          <h1 className="mt-2 text-3xl font-bold leading-tight tracking-tight sm:text-4xl">Check your project on MahaRERA</h1>
          <p className="mt-3 text-lg text-slate-200">Bought a flat, or planning to? See the possession date, whether it moved, and how many homes are booked.</p>
        </div>
      </div>
      <div className="mx-auto -mt-7 max-w-xl px-4 pb-12">
        <CheckSearch initialQ={q} initialHits={hits} />
        <section aria-labelledby="shows-title" className="mt-10">
          <h2 id="shows-title" className="text-lg font-semibold text-slate-900">What you will see</h2>
          <ul className="mt-3 list-none space-y-3 p-0">
            {SHOWS.map(([t, d]) => (
              <li key={t} className="flex gap-3">
                <span aria-hidden className="mt-1 inline-flex h-6 w-6 flex-none items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">✓</span>
                <span className="text-slate-700"><span className="font-semibold text-slate-900">{t}</span>: {d}</span>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-sm text-slate-600">
            From MahaRERA&apos;s public records for Pune district, read again as they change. MahaRERA does not publish construction
            progress, so we do not guess it: for your flat, the possession date in your agreement is the one that counts.
          </p>
        </section>
        <div className="mt-8"><InstallApp /></div>
      </div>
    </MarketingShell>
  )
}
