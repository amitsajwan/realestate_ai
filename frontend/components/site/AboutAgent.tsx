import React from 'react'
import type { AgentProfile } from '@/lib/site/types'
import { MAHARERA_URL, displayName, safeImage, safeRera } from '@/lib/site/theme'
import SocialLinks from './SocialLinks'
import { BRAND_NAME } from '@/lib/brand'

/** About section of the agent's own page: photo/logo, about text, areas, languages, experience and the self-declared RERA agent number. */
export default function AboutAgent({ agent }: { agent: AgentProfile }) {
  const b = agent.branding_data
  const name = displayName(agent)
  const logo = safeImage(b?.logo)
  const rera = safeRera(b?.rera_agent_no)
  const about = (b?.about || '').trim() || (agent.bio || '').trim()
  const areas = b?.areas || []
  const languages = (b?.languages && b.languages.length ? b.languages : agent.languages) || []
  const years = b?.years_experience
  return (
    <section id="about" aria-labelledby="about-title" className="scroll-mt-16">
      <h2 id="about-title" className="mb-3 text-2xl font-bold">About {name}</h2>
      {(agent.photo || logo) && (
        <div className="mb-3 flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {agent.photo && <img src={agent.photo} alt={'Photo of ' + agent.agent_name} width={64} height={64} className="h-16 w-16 rounded-full object-cover" />}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {logo && <img src={logo} alt={name + ' logo'} height={48} className="h-12 w-auto max-w-[9rem] object-contain" />}
        </div>
      )}
      {about && <p className="leading-relaxed text-slate-800">{about}</p>}
      {areas.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-sm font-semibold text-slate-700">Areas we cover</p>
          <ul className="flex list-none flex-wrap gap-2 p-0" aria-label="Areas we cover">
            {areas.map((a) => (
              <li key={a} className="rounded-full border px-3 py-1 text-sm font-medium" style={{ borderColor: 'var(--site-primary)', color: 'var(--site-primary)' }}>{a}</li>
            ))}
          </ul>
        </div>
      )}
      <SocialLinks instagram={b?.social?.instagram} facebook={b?.social?.facebook} />
      {(agent.specialties || []).length > 0 && (
        <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
          {(agent.specialties || []).map((s) => (
            <li key={s} className="rounded-full bg-slate-100 px-3 py-1 text-sm">{s}</li>
          ))}
        </ul>
      )}
      <dl className="mt-4 space-y-1 text-sm text-slate-700">
        {languages.length > 0 && <div><dt className="inline font-semibold">Speaks: </dt><dd className="inline">{languages.join(', ')}</dd></div>}
        {years ? <div><dt className="inline font-semibold">Experience: </dt><dd className="inline">{years} {years === 1 ? 'year' : 'years'}</dd></div>
          : agent.experience ? <div><dt className="inline font-semibold">Experience: </dt><dd className="inline">{agent.experience}</dd></div> : null}
      </dl>
      {rera && (
        <p data-testid="rera-agent" className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800">
          <span className="font-semibold">RERA agent registration: {rera}</span>
          <span className="block text-slate-600">This number is stated by the agent. {BRAND_NAME} has not verified it.{' '}
            <a href={MAHARERA_URL} target="_blank" rel="noopener noreferrer" className="font-semibold underline underline-offset-2" style={{ color: 'var(--site-primary)' }}>Check it on MahaRERA</a>.
          </span>
        </p>
      )}
    </section>
  )
}
