import React from 'react'
import Link from 'next/link'

/** The way into the home plan, on East Pune pages and /projects. A link, not the form: the questions have their own page. */
export default function HomePlanBox({ area }: { area?: string | null }) {
  return (
    <aside className="rounded-2xl border border-[#f0b440] bg-[#fff8e8] p-5" data-testid="home-plan-box">
      <h2 className="text-xl font-bold text-slate-900">Not sure which project suits your family?</h2>
      <p className="mt-1 text-slate-800">
        Answer six questions and get a free shortlist of East Pune projects{area ? `, ${area} included,` : ''} picked on MahaRERA
        facts, with the reasons and what to check on the visit.
      </p>
      <Link href="/home-plan" className="mt-3 inline-flex min-h-[48px] items-center rounded-full bg-[#0f2340] px-6 font-bold text-white no-underline">
        Get my home plan
      </Link>
    </aside>
  )
}
