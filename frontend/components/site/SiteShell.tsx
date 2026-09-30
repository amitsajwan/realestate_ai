import React from 'react'
import Link from 'next/link'
import { agentPath } from '@/lib/site/slug'
import { themeVars } from '@/lib/site/theme'
import type { AgentProfile } from '@/lib/site/types'
import ChatWidget from './ChatWidget'

/** Server-rendered wrapper in the PUNE Property brand (navy + gold, PP logo). Theme variables come from lib/site/theme. */
export default function SiteShell({ agent, children, bottomPad = false }: { agent: AgentProfile; children: React.ReactNode; bottomPad?: boolean }) {
  return (
    <div data-surface="v2" style={themeVars(agent.branding_data) as React.CSSProperties} className="min-h-screen bg-white text-slate-900" lang="en">
      <header className="sticky top-0 z-30 border-b border-[#1d3a63] bg-[var(--site-primary)] text-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-2">
          <Link href={agentPath(agent.slug)} className="flex min-h-[44px] items-center gap-2 font-bold text-white no-underline sm:gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/brand/logo.png" alt="" width={36} height={36} className="h-9 w-9 rounded-full" />
            <span className="whitespace-nowrap text-[15px] leading-tight sm:text-base">PUNE Property<span className="hidden text-[11px] font-medium text-[var(--site-accent)] sm:block">Find. Compare. Decide.</span></span>
          </Link>
          <nav aria-label="Site" className="flex text-sm">
            <a href={agentPath(agent.slug) + '#listings'} className="hidden sm:flex min-h-[44px] items-center px-2 text-white/90 no-underline sm:px-3">Properties</a>
            <a href={agentPath(agent.slug) + '#guides'} className="flex min-h-[44px] items-center px-2 text-white/90 no-underline sm:px-3">Guides</a>
            <a href={agentPath(agent.slug) + '#contact'} className="flex min-h-[44px] items-center px-2 text-white/90 no-underline sm:px-3">Contact</a>
          </nav>
        </div>
      </header>
      <div id="site-main" className={bottomPad ? 'pb-24 md:pb-0' : ''}>{children}</div>
      <ChatWidget agentSlug={agent.slug} />
      <footer className="bg-[var(--site-secondary)] px-4 py-8 text-center text-sm text-slate-300">
        <p className="font-semibold text-white">PUNE Property</p>
        <p className="mt-1 text-[var(--site-accent)]">Find. Compare. Decide.</p>
        <p className="mt-3">&copy; {new Date().getFullYear()} PUNE Property. All rights reserved.</p>
      </footer>
    </div>
  )
}
