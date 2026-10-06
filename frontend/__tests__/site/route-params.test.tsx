/**
 * Regression (Next 15+): dynamic route `params` are a Promise. Reading `params.slug` synchronously gives undefined, which made
 * every agent site a 404 right after the upgrade (the build did not catch it; only a browser run did).
 */
process.env.SITE_USE_FIXTURES = '1'

jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NEXT_NOT_FOUND') },
  permanentRedirect: (url: string) => { throw new Error('NEXT_REDIRECT ' + url) },
}))

import AgentHomePage from '@/app/agent/[slug]/page'
import ListingPage from '@/app/agent/[slug]/listings/[id]/page'
import LegacyListingPage from '@/app/listings/[id]/page'

describe('agent site pages take async route params', () => {
  it('renders the home page for a known agent', async () => {
    const el = await AgentHomePage({ params: Promise.resolve({ slug: 'demo' }) })
    expect(el).toBeTruthy()
  })

  it('an unknown agent is the only case that is "not found"', async () => {
    await expect(AgentHomePage({ params: Promise.resolve({ slug: 'nobody-here' }) })).rejects.toThrow('NEXT_NOT_FOUND')
  })

  it('renders a listing page for a known agent and listing', async () => {
    const { fixtureListings } = await import('@/lib/site/fixtures')
    const first = (fixtureListings('demo') as { items: { id: string }[] }).items[0]
    const el = await ListingPage({ params: Promise.resolve({ slug: 'demo', id: first.id }) })
    expect(el).toBeTruthy()
  })

  it('redirects the old listing share URL to the owning agent page', async () => {
    await expect(LegacyListingPage({
      params: Promise.resolve({ id: 'fx-baner-2bhk' }),
      searchParams: Promise.resolve({ src: 'whatsapp' }),
    })).rejects.toThrow('NEXT_REDIRECT /agent/demo/listings/fx-baner-2bhk?src=whatsapp')
  })
})
