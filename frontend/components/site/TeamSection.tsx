import React from 'react'
import type { AgentProfile } from '@/lib/site/types'
import { displayName, safeImage } from '@/lib/site/theme'
import { shownPhone, whatsappLink } from '@/lib/site/links'
import TrackedLink from './TrackedLink'

/**
 * The office's people, from branding_data.team. Each card asks for that person by name: on WhatsApp to the office number
 * when the agent's phone may be shown, otherwise through the enquiry form on the same page.
 */
export default function TeamSection({ agent }: { agent: AgentProfile }) {
  const team = (agent.branding_data?.team || []).filter((m) => m && (m.name || '').trim())
  if (!team.length) return null
  const name = displayName(agent)
  const phone = shownPhone(agent)
  const btn = 'mt-3 inline-flex min-h-[44px] items-center justify-center rounded-xl px-4 font-semibold text-white no-underline'
  return (
    <section id="team" aria-labelledby="team-title" className="scroll-mt-16">
      <h2 id="team-title" className="mb-4 text-2xl font-bold">Meet the team</h2>
      <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 md:grid-cols-3">
        {team.map((m) => {
          const photo = safeImage(m.photo)
          const first = m.name.trim().split(/\s+/)[0]
          const wa = phone ? whatsappLink(agent.phone, `Hi ${name}, I would like to talk to ${m.name.trim()}.`) : null
          return (
            <li key={m.name} className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {photo && <img src={photo} alt={m.name} loading="lazy" className="aspect-square w-full bg-slate-100 object-cover object-top" />}
              <div className="flex flex-1 flex-col px-4 pb-4 pt-3">
                <h3 className="text-lg font-semibold text-slate-900">{m.name}</h3>
                {m.role && <p className="text-sm font-bold text-[var(--site-accent-text)]">{m.role}</p>}
                {m.about && <p className="mt-1 flex-1 text-sm text-slate-600">{m.about}</p>}
                {wa ? (
                  <TrackedLink href={wa} event="whatsapp_click" agentSlug={agent.slug} target="_blank" rel="noopener noreferrer" className={btn} style={{ background: 'var(--site-primary)' }}>
                    WhatsApp {first}
                  </TrackedLink>
                ) : (
                  <a href="#enquire" className={btn} style={{ background: 'var(--site-primary)' }}>Ask {first}</a>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
