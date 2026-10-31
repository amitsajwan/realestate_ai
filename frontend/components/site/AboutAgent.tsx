import React from 'react'
import type { AgentProfile } from '@/lib/site/types'
import { MAHARERA_URL, displayName, safeImage, safeRera } from '@/lib/site/theme'
import { shownPhone } from '@/lib/site/links'
import HiddenPhone from './HiddenPhone'
import { BRAND_NAME } from '@/lib/brand'

const EMAIL = /^[^\s@<>"]{1,64}@[A-Za-z0-9.-]{1,120}\.[A-Za-z]{2,}$/

/**
 * About section of the agent's own page. Left: photo/logo, about text, what the office does, areas, languages, experience.
 * Right, when the agent has any of them: an office card with address, phone (only when shownPhone allows), e-mail, the
 * self-declared RERA agent number and the enquiry button. Social links are in the footer (SiteShell), not repeated here.
 */
export default function AboutAgent({ agent }: { agent: AgentProfile }) {
  const b = agent.branding_data
  const name = displayName(agent)
  const logo = safeImage(b?.logo)
  const rera = safeRera(b?.rera_agent_no)
  const about = (b?.about || '').trim() || (agent.bio || '').trim()
  const areas = b?.areas || []
  const services = (b?.services || []).filter((s) => s && s.trim())
  const languages = (b?.languages && b.languages.length ? b.languages : agent.languages) || []
  const years = b?.years_experience
  const address = (agent.office_address || '').trim()
  const phone = shownPhone(agent)
  const email = agent.email && EMAIL.test(agent.email.trim()) ? agent.email.trim() : null
  const office = !!(address || phone || email || rera)
  return (
    <section id="about" aria-labelledby="about-title" className="scroll-mt-16">
      <h2 id="about-title" className="mb-3 text-2xl font-bold">About {name}</h2>
      <div className={office ? 'grid gap-8 md:grid-cols-[1.4fr_1fr]' : ''}>
        <div className="min-w-0">
          {/* the office card carries the logo; without one the logo sits here */}
          {(agent.photo || (logo && !office)) && (
            <div className="mb-3 flex items-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {agent.photo && <img src={agent.photo} alt={'Photo of ' + agent.agent_name} width={64} height={64} className="h-16 w-16 rounded-full object-cover" />}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {logo && !office && <img src={logo} alt={name + ' logo'} height={48} className="h-12 w-auto max-w-[9rem] object-contain" />}
            </div>
          )}
          {about && about.split(/\n\s*\n/).map((p, i) => <p key={i} className="mb-3 max-w-prose leading-relaxed text-slate-800">{p.trim()}</p>)}
          {services.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-sm font-semibold text-slate-700">What we do for you</p>
              <ul className="grid list-none gap-2 p-0 sm:grid-cols-2" aria-label="What we do for you">
                {services.map((s) => (
                  <li key={s} className="flex gap-2 text-slate-800">
                    <span aria-hidden className="mt-1.5 h-3 w-3 shrink-0 rounded-sm" style={{ background: 'var(--site-accent)' }} />{s}
                  </li>
                ))}
              </ul>
            </div>
          )}
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
        </div>

        {office && (
          <aside aria-label="Office details" className="self-start overflow-hidden rounded-2xl border border-slate-200">
            <div className="flex items-center gap-3 px-4 py-3 font-semibold text-white" style={{ background: 'var(--site-primary)' }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {logo && <img src={logo} alt="" height={32} className="h-8 w-auto max-w-[6rem] rounded bg-white object-contain p-0.5" />}
              <span>{name}</span>
            </div>
            <dl className="grid gap-3 px-4 py-4">
              {address && <div><dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Office</dt><dd className="font-semibold text-slate-900">{address}</dd></div>}
              {phone && (
                <div><dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Phone</dt>
                  <dd><HiddenPhone code={phone} agentSlug={agent.slug} className="font-semibold text-slate-900" /></dd></div>
              )}
              {email && <div><dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Email</dt><dd className="break-all font-semibold text-slate-900">{email}</dd></div>}
            </dl>
            {rera && (
              <p data-testid="rera-agent" className="mx-4 mb-4 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800">
                <span className="font-semibold">RERA agent registration: {rera}</span>
                <span className="block text-slate-600">This number is stated by the agent. {BRAND_NAME} has not verified it.{' '}
                  <a href={MAHARERA_URL} target="_blank" rel="noopener noreferrer" className="font-semibold underline underline-offset-2" style={{ color: 'var(--site-primary)' }}>Check it on MahaRERA</a>.
                </span>
              </p>
            )}
            <a href="#enquire" className="mx-4 mb-4 flex min-h-[44px] items-center justify-center rounded-xl font-semibold text-white no-underline"
              style={{ background: 'var(--site-primary)' }}>Send an enquiry</a>
          </aside>
        )}
      </div>
    </section>
  )
}
