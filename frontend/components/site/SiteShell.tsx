import React from 'react'
import Link from 'next/link'
import { agentPath } from '@/lib/site/slug'
import { displayName, monogram, resolveTheme, safeImage, safeRera, themeVars, MAHARERA_URL } from '@/lib/site/theme'
import type { AgentProfile } from '@/lib/site/types'
import ChatWidget from './ChatWidget'
import ContactBlock from '@/components/marketing/ContactBlock'

/** Server-rendered wrapper in the AGENT's own brand (preset colours, logo or monogram, business name). Footer carries a small 'Powered by PUNE Property'. */
export default function SiteShell({ agent, children, bottomPad = false }: { agent: AgentProfile; children: React.ReactNode; bottomPad?: boolean }) {
  const b = agent.branding_data
  const t = resolveTheme(b)
  const name = displayName(agent)
  const logo = safeImage(b?.logo)
  const rera = safeRera(b?.rera_agent_no)
  const light = t.id === 'cream-ink'
  const home = agentPath(agent.slug)
  const link = 'flex min-h-[44px] items-center px-2 no-underline sm:px-3 opacity-90'
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
            <a href={home + '#contact'} className={link} style={{ color: 'inherit' }}>Contact</a>
          </nav>
        </div>
      </header>
      <div id="site-main" className={bottomPad ? 'pb-24 md:pb-0' : ''}>{children}</div>
      <ChatWidget agentSlug={agent.slug} />
      <footer className="bg-[var(--site-secondary)] px-4 py-8 text-center text-sm text-slate-300">
        <p className="font-semibold text-white">{name}</p>
        {b?.tagline && <p className="mt-1 text-[var(--site-accent)]">{b.tagline}</p>}
        {rera && (
          <p className="mt-2 text-slate-300">
            RERA agent registration: <span className="font-semibold text-white">{rera}</span> (as stated by the agent; not verified by PUNE Property).{' '}
            <a href={MAHARERA_URL} target="_blank" rel="noopener noreferrer" className="text-white underline underline-offset-2">Check on MahaRERA</a>
          </p>
        )}
        <div className="mx-auto mt-5 flex max-w-md flex-col items-center text-center">
          <ContactBlock tone="dark" />
        </div>
        <p className="mt-3">&copy; {new Date().getFullYear()} {name}</p>
        <p className="mt-2 text-xs text-slate-300">Powered by <Link href="/" className="text-white underline underline-offset-2">PUNE Property</Link></p>
      </footer>
    </div>
  )
}
