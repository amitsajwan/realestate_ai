import React from 'react'
import Link from 'next/link'
import { NEWS_TEXT, type NewsArea } from '@/lib/news/data'

/** 'Looking in this area? I am interested': one button per area, to that area's page, plus the link-in-bio page where each post has its own
 *  interest button. No form here and nothing collected on this page. */
export default function InterestStrip({ areas }: { areas: NewsArea[] }) {
  const list = areas.length ? areas : [{ slug: 'kharadi', name: 'Kharadi' }]
  const where = list.map((a) => a.name).join(' or ')
  return (
    <aside aria-label="Interested in this area" data-testid="interest-strip" className="mt-10 rounded-2xl bg-[#0f2340] p-5 text-white sm:p-6">
      <p className="text-lg font-extrabold">{NEWS_TEXT.interestTitle(where)}</p>
      <p className="mt-1 text-slate-100">{NEWS_TEXT.interestLead}</p>
      <div className="mt-4 flex flex-wrap gap-3">
        {list.map((a) => (
          <Link key={a.slug} href={`/localities/${a.slug}`}
            className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-[#f0b440] px-5 font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e]">
            {NEWS_TEXT.interestCta(a.name)}
          </Link>
        ))}
        <Link href="/go" className="inline-flex min-h-[48px] items-center justify-center rounded-xl border border-white/40 px-5 font-semibold text-white no-underline hover:bg-white/10">
          See what we are showing now
        </Link>
      </div>
    </aside>
  )
}
