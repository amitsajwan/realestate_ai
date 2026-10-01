import React from 'react'
import Link from 'next/link'
import { BRAND_NAME } from '@/lib/brand'
import type { AgentProfile } from '@/lib/site/types'

/** True only when the owner marked this profile as the demo (branding_data.demo, an owner-only flag agents cannot set). */
export const isDemoAgent = (agent: Pick<AgentProfile, 'branding_data'> | null | undefined): boolean => agent?.branding_data?.demo === true

export const DEMO_NOTE = `This is a demo page showing what an agent's ${BRAND_NAME} page looks like.`

/**
 * Demo marking for the fictional demo agent: a note under the header and a 'DEMO' ribbon pinned to the corner of the screen
 * (it ignores taps, so nothing under it is blocked). Renders nothing for real agents.
 */
export default function DemoRibbon({ agent }: { agent: Pick<AgentProfile, 'branding_data'> }) {
  if (!isDemoAgent(agent)) return null
  return (
    <>
      <div role="note" aria-label="Demo page" data-testid="demo-note" className="border-b border-amber-300 bg-amber-50 text-amber-950">
        <p className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2.5 text-sm">
          <span className="rounded bg-amber-500 px-2 py-0.5 text-xs font-extrabold tracking-widest text-amber-950">DEMO</span>
          <span>{DEMO_NOTE} The agent is fictional and the homes are labelled samples.</span>
          <Link href="/for-agents" className="font-semibold text-amber-950 underline underline-offset-2">Get a page like this</Link>
        </p>
      </div>
      <div aria-hidden="true" data-testid="demo-ribbon" className="pointer-events-none fixed bottom-0 left-0 z-50 h-[5.5rem] w-[5.5rem] overflow-hidden print:hidden">
        <span className="absolute bottom-[1.05rem] left-[-2.2rem] block w-32 rotate-45 bg-amber-500 py-0.5 pl-[0.3em] text-center text-[11px] font-extrabold tracking-[0.3em] text-amber-950 shadow-md">
          DEMO
        </span>
      </div>
    </>
  )
}
