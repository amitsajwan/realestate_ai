import React from 'react'
import Link from 'next/link'
import { HOME } from '@/lib/marketing/strings'
import { LOCALITIES } from '@/lib/marketing/localities'
import type { Insight } from '@/lib/marketing/insights'
import SectionHead from './SectionHead'
import { wrap } from './shared'

/** One card per locality guide, plus the side-by-side comparison guide when there is one. `children` goes under the cards. */
export default function HomeAreas({ compare, children }: { compare?: Insight; children?: React.ReactNode }) {
  return (
    <section id="areas" aria-labelledby="home-areas-title" className="scroll-mt-16 bg-[#fbf6ea] py-12 sm:py-16">
      <div className={wrap}>
        <SectionHead id="home-areas-title" title={HOME.areas.heading} lead={HOME.areas.lead} more={{ href: '/localities', label: HOME.areas.all }} />
        <ul className="mt-6 grid list-none gap-4 p-0 sm:grid-cols-3">
          {LOCALITIES.map((l) => (
            <li key={l.slug} className="list-none">
              <Link href={`/localities/${l.slug}`} className="flex h-full flex-col rounded-2xl border border-[#ead9ae] border-l-4 border-l-[#f0b440] bg-white p-5 no-underline hover:border-slate-400 hover:border-l-[#f0b440]">
                <h3 className="text-xl font-bold text-[#0f2340]">{l.name}</h3>
                <span className="mt-1 text-sm text-slate-700">{l.tagline}</span>
              </Link>
            </li>
          ))}
        </ul>
        {compare && (
          <p className="mt-4 rounded-2xl bg-white p-4 text-slate-800">
            <span className="font-semibold">{HOME.areas.compareLabel}</span>{' '}
            <Link href={`/insights/${compare.slug}`} className="font-semibold text-[#0f2340] underline underline-offset-2">{compare.title}</Link>
          </p>
        )}
        {children}
      </div>
    </section>
  )
}
