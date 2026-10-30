import React from 'react'
import Link from 'next/link'
import { agentPath } from '@/lib/site/slug'
import { displayName, monogram, resolveTheme, safeImage, safeRera, themeVars, MAHARERA_URL } from '@/lib/site/theme'
import type { AgentProfile } from '@/lib/site/types'
import ChatWidget from './ChatWidget'
import ContactBlock from '@/components/marketing/ContactBlock'
import { BRAND_NAME, isHouseAgent } from '@/lib/brand'
import { shownPhone } from '@/lib/site/links'
import { SocialIcons, agentSocialLinks } from './SocialLinks'

const EMAIL = /^[^\s@<>"]{1,64}@[A-Za-z0-9.-]{1,120}\.[A-Za-z]{2,}$/
const WEBSITE = /^https:\/\/[A-Za-z0-9.-]{1,120}\/?$/

/** Server-rendered wrapper in the AGENT's own brand (preset colours, logo or monogram, business name). Footer carries a small 'Powered by Avasetu'. */
export default function SiteShell({ agent, children, bottomPad = false }: { agent: AgentProfile; children: React.ReactNode; bottomPad?: boolean }) {
  const b = agent.branding_data
  const t = resolveTheme(b)
  const name = displayName(agent)
  const logo = safeImage(b?.logo)
  const rera = safeRera(b?.rera_agent_no)
  const light = t.id === 'cream-ink'
  const home = agentPath(agent.slug)
  const link = 'flex min-h-[44px] items-center px-2 no-underline sm:px-3 opacity-90'
  const hasTeam = (b?.team || []).some((m) => (m?.name || '').trim())
  const address = (agent.office_address || '').trim()
  const phone = shownPhone(agent)
  const email = agent.email && EMAIL.test(agent.email.trim()) ? agent.email.trim() : null
  const social = agentSocialLinks(b?.social)
  const website = b?.website && WEBSITE.test(b.website.trim()) ? b.website.trim() : null
  const fLink = 'text-white underline underline-offset-2'
  return (
    <div data-surface="v2" data-preset={t.id} style={themeVars(b) as React.CSSProperties} className="min-h-screen bg-white text-slate-900" lang="en">
      <header className="sticky top-0 z-30 border-b" style={{ background: 'var(--site-header-bg)', color: 'var(--site-header-fg)', borderColor: light ? 'var(--site-accent)' : 'rgba(255,255,255,.14)' }}>
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-4 py-2">
          <Link href={home} className="flex min-h-[44px] min-w-0 items-center gap-2 font-bold no-underline sm:gap-3" style={{ color: 'inherit' }}>
            {logo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={logo} alt="" height={36} className="h-9 w-auto max-w-[7rem] shrink-0 rounded-md bg-white object-contain p-0.5" />
            ) : (
              <span aria-hidden className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-extrabold" style={{ background: 'var(--site-accent)', color: 'var(--site-on-accent)' }}>{monogram(name)}</span>
            )}
            <span className="min-w-0 leading-tight">
              <span className="block truncate text-[15px] sm:text-base">{name}</span>
              <span className="hidden truncate text-[11px] font-medium opacity-80 sm:block">{name !== agent.agent_name ? agent.agent_name + ' · ' : ''}Property advisor, Pune</span>
            </span>
          </Link>
          <nav aria-label="Site" className="flex shrink-0 text-sm">
            <a href={home + '#listings'} className={'hidden sm:flex ' + link} style={{ color: 'inherit' }}>Properties</a>
            <a href={home + '#about'} className={link} style={{ color: 'inherit' }}>About</a>
            {hasTeam && <a href={home + '#team'} className={'hidden sm:flex ' + link} style={{ color: 'inherit' }}>Team</a>}
            <a href={home + '#contact'} className={link} style={{ color: 'inherit' }}>Contact</a>
          </nav>
        </div>
      </header>
      <div id="site-main" className={bottomPad ? 'pb-24 md:pb-0' : ''}>{children}</div>
      <ChatWidget agentSlug={agent.slug} />
      <footer className="bg-[var(--site-secondary)] px-4 text-sm text-slate-300">
        <div className="mx-auto grid max-w-5xl gap-8 py-9 md:grid-cols-3">
          <div className="min-w-0">
            {logo && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={logo} alt="" height={40} className="mb-2 h-10 w-auto max-w-[8rem] rounded-md bg-white object-contain p-0.5" />
            )}
            <p className="font-semibold text-white">{name}</p>
            {b?.tagline && <p className="mt-1 text-[var(--site-accent)]">{b.tagline}</p>}
            {rera && (
              <p className="mt-3 text-slate-300">
                RERA agent registration: <span className="font-semibold text-white">{rera}</span> (as stated by the agent; not verified by {BRAND_NAME}).{' '}
                <a href={MAHARERA_URL} target="_blank" rel="noopener noreferrer" className={fLink}>Check on MahaRERA</a>
              </p>
            )}
          </div>
          <div className="min-w-0">
            <h2 className="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--site-accent)]">{address || phone || email ? 'Visit or call' : 'On this site'}</h2>
            {address && <p className="font-semibold text-white">{address}</p>}
            {phone && <p className="mt-1"><a href={phone.href} className="text-white no-underline">{phone.text}</a></p>}
            {email && <p className="mt-1 break-all">{email}</p>}
            <ul className="mt-3 grid list-none gap-1 p-0">
              <li><a href={home + '#listings'} className={fLink}>Properties</a></li>
              <li><a href={home + '#about'} className={fLink}>About</a></li>
              {hasTeam && <li><a href={home + '#team'} className={fLink}>Team</a></li>}
              <li><a href={home + '#contact'} className={fLink}>Contact</a></li>
            </ul>
          </div>
          {(social.length > 0 || website) && (
            <div className="min-w-0">
              <h2 className="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--site-accent)]">Follow {name}</h2>
              <SocialIcons links={social} />
              {website && <p className="mt-3">Website: <a href={website} target="_blank" rel="noopener noreferrer" className={fLink}>{website.replace(/^https:\/\/(www\.)?/, '').replace(/\/$/, '')}</a></p>}
            </div>
          )}
        </div>
        <div className="mx-auto max-w-5xl border-t border-white/10 py-6 text-center">
          <div className="mx-auto flex max-w-md flex-col items-center text-center">
            <ContactBlock tone="dark" invite={false} />
          </div>
          <p className="mt-3">&copy; {new Date().getFullYear()} {name}</p>
          {/* an agent's site credits the agents' home; the team's own site is Avasetu, so its credit is the buyers' home */}
          <p className="mt-2 text-xs text-slate-300">Powered by <Link href={isHouseAgent(agent.slug) ? '/' : '/agents'} className="text-white underline underline-offset-2">{BRAND_NAME}</Link></p>
        </div>
      </footer>
    </div>
  )
}
