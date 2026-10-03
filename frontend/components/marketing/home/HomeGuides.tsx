import React from 'react'
import Link from 'next/link'
import { HOME } from '@/lib/marketing/strings'
import type { Insight } from '@/lib/marketing/insights'
import SectionHead from './SectionHead'
import { wrap } from './shared'

/** Buyer guides (the /insights articles). */
export default function HomeGuides({ guides }: { guides: Insight[] }) {
  if (!guides.length) return null
  return (
    <section id="guides" aria-labelledby="home-guides-title" className="scroll-mt-16 bg-slate-50 py-12 sm:py-16">
      <div className={wrap}>
        <SectionHead id="home-guides-title" title={HOME.guides.heading} lead={HOME.guides.lead} more={{ href: '/insights', label: HOME.guides.all }} />
        <ul className="mt-6 grid list-none gap-4 p-0 md:grid-cols-2">
          {guides.map((g) => (
            <li key={g.slug} className="list-none">
              <Link href={`/insights/${g.slug}`} className="block h-full rounded-2xl border border-slate-200 bg-white p-5 no-underline hover:border-slate-400">
                <h3 className="text-lg font-bold text-[#0f2340]">{g.title}</h3>
                <p className="mt-2 leading-relaxed text-slate-700">{g.summary}</p>
                <p className="mt-3 text-sm text-slate-600">Updated {g.updatedLabel}</p>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
