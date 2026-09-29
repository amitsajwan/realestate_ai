import React from 'react'
import { whatsappMessage } from '@/lib/site/links'
import type { AgentProfile } from '@/lib/site/types'
import ContactButtons from './ContactButtons'

export default function Hero({ agent, city }: { agent: AgentProfile; city: string }) {
  const tagline = agent.branding_data && agent.branding_data.tagline
  return (
    <section aria-labelledby="hero-title" className="bg-[var(--site-primary)] text-[var(--site-on-primary)]">
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-5 px-4 py-10 text-center md:flex-row md:text-left">
        {agent.photo && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={agent.photo} alt={'Photo of ' + agent.agent_name} width={144} height={144} loading="eager"
            className="h-32 w-32 rounded-full border-4 border-white/70 object-cover md:h-36 md:w-36" />
        )}
        <div className="flex-1">
          <h1 id="hero-title" className="text-3xl font-extrabold leading-tight">{agent.agent_name}</h1>
          {tagline && <p className="mt-2 text-lg opacity-95">{tagline}</p>}
          {city && <p className="mt-1 text-sm opacity-90">Real estate advisor in {city}</p>}
          <div className="mt-5 max-w-md">
            <ContactButtons agentSlug={agent.slug} phone={agent.phone} waMessage={whatsappMessage(agent.agent_name)} />
          </div>
        </div>
      </div>
    </section>
  )
}
