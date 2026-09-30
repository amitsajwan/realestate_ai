import React from 'react'
import type { AgentProfile } from '@/lib/site/types'
import ContactButtons from './ContactButtons'
import Skyline from './Skyline'
import { whatsappMessage } from '@/lib/site/links'

export default function Hero({ agent, city }: { agent: AgentProfile; city: string }) {
  return (
    <section aria-labelledby="hero-title" className="bg-gradient-to-b from-[#102340] to-[#183a5d] text-white">
      <div className="mx-auto max-w-5xl px-4 pb-6 pt-12 text-center sm:pt-16 sm:text-left">
        <p className="inline-block rounded-full bg-[var(--site-accent)] px-4 py-1 text-xs font-bold uppercase tracking-wide text-[#18202c]">{city ? city + ' property' : 'Property'}</p>
        <h1 id="hero-title" className="mt-4 text-4xl font-extrabold leading-tight sm:text-5xl">Homes in Pune, shared clearly</h1>
        <p className="mt-3 max-w-xl text-lg text-slate-200">Price, area, possession and RERA in one place. Tell us what you are looking for and we will send you the details.</p>
        <div className="mt-7 flex flex-col gap-3 sm:flex-row">
          <a href="#enquire" className="inline-flex min-h-[52px] items-center justify-center rounded-full bg-[var(--site-accent)] px-8 text-lg font-bold text-[#18202c] no-underline">I&apos;m interested</a>
          <a href="#guides" className="inline-flex min-h-[52px] items-center justify-center rounded-full border-2 border-white/70 px-8 text-lg font-semibold text-white no-underline">Read our guides</a>
        </div>
        <div className="mt-5 max-w-md"><ContactButtons agentSlug={agent.slug} phone={agent.phone} waMessage={whatsappMessage(agent.agent_name)} /></div>
      </div>
      <Skyline />
    </section>
  )
}
