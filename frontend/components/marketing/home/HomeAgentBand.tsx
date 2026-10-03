import React from 'react'
import Link from 'next/link'
import { HOME } from '@/lib/marketing/strings'
import { demoAgentPath } from '@/lib/brand'
import { wrap } from './shared'

/** A compact pointer for agents: the full story (and the invite form) lives on /for-agents. */
export default function HomeAgentBand() {
  const A = HOME.agents
  return (
    <section aria-labelledby="home-agents-title" className="bg-[#0f2340] py-8 text-white">
      <div className={wrap + ' sm:flex sm:items-center sm:justify-between sm:gap-6'}>
        <div>
          <h2 id="home-agents-title" className="text-lg font-extrabold">{A.title}</h2>
          <p className="mt-1 text-slate-100">{A.body}</p>
        </div>
        <div className="mt-4 flex flex-wrap gap-3 sm:mt-0 sm:flex-none">
          <Link href="/for-agents" className="inline-flex min-h-[48px] items-center justify-center rounded-xl bg-[#f0b440] px-6 font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e]">{A.cta}</Link>
          <Link href={demoAgentPath()} className="inline-flex min-h-[48px] items-center justify-center rounded-xl border border-white/50 px-5 font-semibold text-white no-underline hover:bg-white/10">{A.demo}</Link>
        </div>
      </div>
    </section>
  )
}
