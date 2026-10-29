import React from 'react'
import { render, screen } from '@testing-library/react'
import SiteShell from '@/components/site/SiteShell'
import { FIXTURE_BRAND_AGENTS } from '@/lib/site/fixtures'
import { agentJsonLd, agentMetadata } from '@/lib/site/seo'
import { metadata as trial } from '@/app/trial/page'
import { metadata as invite } from '@/app/request-invite/page'
import { metadata as agentsHome } from '@/app/agents/page'
import type { AgentProfile } from '@/lib/site/types'

jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))

// Google answered "avasetu pune" with the team's own agent site, then the agents' trial page (2026-10-29). The buyers' home is
// the brand's page now: the team's site hands its canonical to it, and the agents' sign-up pages stay out of search.
const joshi = FIXTURE_BRAND_AGENTS['meera-joshi-kothrud']
const house = { ...joshi, slug: 'avasetu', agent_name: 'Avasetu Homes' } as AgentProfile

describe("the team's own agent site", () => {
  it("names the buyers' home as its canonical page; another agent's site keeps its own", () => {
    expect(agentMetadata(house, [], 'Pune').alternates?.canonical).toBe(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000')
    expect(String(agentMetadata(joshi, [], 'Pune').alternates?.canonical)).toMatch(/\/agent\/meera-joshi-kothrud$/)
    expect(agentMetadata(house, [], 'Pune').robots).toBeUndefined()   // still served and followed, never a noindex or a redirect
  })

  it('belongs to the Avasetu organisation in its structured data; another agent does not', () => {
    expect(agentJsonLd(house, 'Pune').parentOrganization).toMatchObject({ '@type': 'Organization', name: 'Avasetu' })
    expect(agentJsonLd(joshi, 'Pune').parentOrganization).toBeUndefined()
  })

  it("credits Avasetu with a link to the buyers' home, while an agent's site credits the agents' home", () => {
    const { unmount } = render(<SiteShell agent={house}><p>body</p></SiteShell>)
    expect(screen.getByRole('link', { name: 'Avasetu' })).toHaveAttribute('href', '/')
    unmount()
    render(<SiteShell agent={joshi}><p>body</p></SiteShell>)
    expect(screen.getByRole('link', { name: 'Avasetu' })).toHaveAttribute('href', '/agents')
  })
})

describe("the agents' pages", () => {
  it('keep the trial and invite pages out of search, and put the brand last on the agents home', () => {
    expect(trial.robots).toEqual({ index: false, follow: true })
    expect(invite.robots).toEqual({ index: false, follow: true })
    expect(agentsHome.robots).toBeUndefined()
    expect(String(agentsHome.title)).toBe('Free trial for real estate agents in Pune | Avasetu')
  })
})
