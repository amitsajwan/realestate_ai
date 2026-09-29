import React from 'react'
import Link from 'next/link'
import { agentPath } from '@/lib/site/slug'
import { themeVars } from '@/lib/site/theme'
import type { AgentProfile } from '@/lib/site/types'

/** Server-rendered wrapper: theme CSS variables come from branding_data, never localStorage. */
export default function SiteShell({ agent, children, bottomPad = false }: { agent: AgentProfile; children: React.ReactNode; bottomPad?: boolean }) {
  return (
    <div style={themeVars(agent.branding_data) as React.CSSProperties} className="min-h-screen bg-white text-slate-900" lang="en">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-2">
          <Link href={agentPath(agent.slug)} className="flex min-h-[44px] items-center gap-2 font-bold text-[var(--site-primary)] no-underline">
            {agent.photo && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={agent.photo} alt="" width={32} height={32} className="h-8 w-8 rounded-full object-cover" />
            )}
            {agent.agent_name}
          </Link>
          <nav aria-label="Site" className="flex gap-1 text-sm">
            <a href={agentPath(agent.slug) + '#listings'} className="flex min-h-[44px] items-center px-3 text-slate-700 no-underline">Properties</a>
            <a href={agentPath(agent.slug) + '#contact'} className="flex min-h-[44px] items-center px-3 text-slate-700 no-underline">Contact</a>
          </nav>
        </div>
      </header>
      <div id="site-main" className={bottomPad ? 'pb-24 md:pb-0' : ''}>{children}</div>
      <footer className="border-t border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-600">
        <p>&copy; {new Date().getFullYear()} {agent.agent_name}. All rights reserved.</p>
      </footer>
    </div>
  )
}
