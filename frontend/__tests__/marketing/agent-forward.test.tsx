import React from 'react'
import { render } from '@testing-library/react'
import AgentsPage from '@/app/agents/page'
import { AGENT_ANCHORS, agentAnchorForward } from '@/components/marketing/siteLinks'

jest.mock('@/components/site/PostsSection', () => ({ __esModule: true, default: () => null }))
jest.mock('@/components/news/NewsSection', () => ({ __esModule: true, default: () => null }))

/** Runs the home page's forwarding script against a pretend address; returns where it sent the visitor, or null. */
function forward(hash: string): string | null {
  let went: string | null = null
  const location = { hash, replace: (to: string) => { went = to } }
  new Function('location', agentAnchorForward())(location)
  return went
}

describe("old links to the agents' sections of the home page", () => {
  it.each(['#invite', '#faq', '#cost', '#what-it-does', '#live', '#hero-ctas', '#lp-name'])('/%s goes on to /agents with the same section', (hash) => {
    expect(forward(hash)).toBe('/agents' + hash)
  })

  it.each(['', '#', '#home-title', '#areas-title', '#invite-x'])('/%s stays on the buyers\' home', (hash) => {
    expect(forward(hash)).toBeNull()
  })

  it('forwards only to sections that exist on /agents', () => {
    const { container } = render(<AgentsPage />)
    for (const id of AGENT_ANCHORS) expect(container.querySelector(`[id="${id}"]`)).not.toBeNull()
  })
})
