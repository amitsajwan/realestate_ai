import React from 'react'
import Link from 'next/link'
import { TRIAL_PATH } from '@/lib/marketing/trial'

/** For agents who land on buyer-facing guides: the free-trial offer, no result claims. */
export default function AgentStrip() {
  return (
    <aside aria-label="For agents" className="mt-10 rounded-2xl bg-[#0f2340] p-5 text-white sm:flex sm:items-center sm:justify-between sm:gap-6">
      <div>
        <p className="text-lg font-extrabold">Are you a real estate agent in Pune?</p>
        <p className="mt-1 text-slate-100">See how a buyer's &quot;INTERESTED&quot; comment becomes a lead card you can act on. Free trial, no card.</p>
      </div>
      <Link href={TRIAL_PATH} className="mt-4 inline-flex min-h-[48px] flex-none items-center justify-center rounded-xl bg-[#f0b440] px-6 font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e] sm:mt-0">
        Claim your free trial
      </Link>
    </aside>
  )
}
