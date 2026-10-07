process.env.SITE_USE_FIXTURES = '1'

import React from 'react'
import { render, screen } from '@testing-library/react'
import DemoRibbon, { DEMO_NOTE, isDemoAgent } from '@/app/agent/[slug]/DemoRibbon'
import AgentHomePage from '@/app/agent/[slug]/page'
import ListingPage from '@/app/agent/[slug]/listings/[id]/page'
import { FIXTURE_BRAND_AGENTS, fixtureListings } from '@/lib/site/fixtures'

jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NEXT_NOT_FOUND') }, usePathname: () => '/', useRouter: () => ({ push: jest.fn() }) }))

describe('DEMO ribbon', () => {
  it('shows the ribbon and the note only when branding_data.demo is exactly true', () => {
    expect(isDemoAgent({ branding_data: { demo: true } })).toBe(true)
    for (const b of [null, {}, { demo: false }, { demo: 'true' as unknown as boolean }]) expect(isDemoAgent({ branding_data: b })).toBe(false)

    const { container, rerender } = render(<DemoRibbon agent={{ branding_data: { demo: true } }} />)
    expect(screen.getByTestId('demo-ribbon')).toHaveTextContent('DEMO')
    expect(screen.getByRole('note')).toHaveTextContent(DEMO_NOTE)
    expect(DEMO_NOTE).toBe("This is a demo page showing what an agent's Avasetu page looks like.")
    expect(screen.getByRole('link', { name: /get a page like this/i })).toHaveAttribute('href', '/for-agents')

    rerender(<DemoRibbon agent={{ branding_data: { business_name: 'Kulkarni Homes' } }} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('appears on the demo agent home and listing pages, not on a real agent page', async () => {
    const { unmount } = render(await AgentHomePage({ params: Promise.resolve({ slug: 'demo' }) }))
    expect(screen.getByTestId('demo-ribbon')).toBeInTheDocument()
    expect(screen.getByText(/demo page showing what an agent/i)).toBeInTheDocument()
    unmount()

    const first = fixtureListings('demo')!.items[0]
    expect(first.title.startsWith('Sample: ')).toBe(true)
    const listing = render(await ListingPage({ params: Promise.resolve({ slug: 'demo', id: first.id }) }))
    expect(screen.getByTestId('demo-ribbon')).toBeInTheDocument()
    listing.unmount()

    render(await AgentHomePage({ params: Promise.resolve({ slug: 'rohan-kulkarni-aundh' }) }))
    expect(screen.queryByTestId('demo-ribbon')).toBeNull()
  })

  it('the demo fixture has no phone number and no RERA number', () => {
    const demo = FIXTURE_BRAND_AGENTS.demo
    expect(demo.phone).toBeNull()
    expect(demo.branding_data?.rera_agent_no).toBeUndefined()
    expect(fixtureListings('demo')!.items.every((l) => !l.rera_no)).toBe(true)
  })
})
