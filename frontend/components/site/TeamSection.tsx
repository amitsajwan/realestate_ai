import React from 'react'
import type { AgentProfile } from '@/lib/site/types'
import { displayName, monogram, safeImage } from '@/lib/site/theme'

/**
 * The office's people, from branding_data.team, as small round portraits beside name and role (owner, 2026-10-30: the first
 * version's full-width square photos filled a phone screen each). Each card asks for that person through the enquiry form on
 * the same page, so the buyer becomes a lead and the agent gets it on WhatsApp through Avasetu.
 */
export default function TeamSection({ agent }: { agent: AgentProfile }) {
  const team = (agent.branding_data?.team || []).filter((m) => m && (m.name || '').trim())
  if (!team.length) return null
  const name = displayName(agent)
  return (
    <section id="team" aria-labelledby="team-title" className="scroll-mt-16">
      <h2 id="team-title" className="text-2xl font-bold">Meet the team</h2>
      <p className="mb-4 mt-1 text-slate-600">The people at {name} who will call you back.</p>
      <ul className="grid list-none gap-3 p-0 md:grid-cols-3">
        {team.map((m) => {
          const photo = safeImage(m.photo)
          const first = m.name.trim().split(/\s+/)[0]
          return (
            <li key={m.name} className="flex items-start gap-4 rounded-2xl border border-slate-200 bg-white p-4">
              {photo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={photo} alt={m.name} width={72} height={72} loading="lazy"
                  className="h-[72px] w-[72px] shrink-0 rounded-full object-cover object-top ring-2 ring-[var(--site-accent)] ring-offset-2" />
              ) : (
                <span aria-hidden className="flex h-[72px] w-[72px] shrink-0 items-center justify-center rounded-full text-lg font-extrabold"
                  style={{ background: 'var(--site-accent)', color: 'var(--site-on-accent)' }}>{monogram(m.name)}</span>
              )}
              <div className="min-w-0">
                <h3 className="font-semibold leading-tight text-slate-900">{m.name}</h3>
                {m.role && <p className="text-sm font-bold text-[var(--site-accent-text)]">{m.role}</p>}
                {m.about && <p className="mt-1 text-sm leading-snug text-slate-600">{m.about}</p>}
                <a href="#enquire" className="mt-2 inline-flex min-h-[36px] items-center text-sm font-semibold text-[var(--site-primary)] underline-offset-4 hover:underline">
                  Ask {first} &rarr;
                </a>
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
