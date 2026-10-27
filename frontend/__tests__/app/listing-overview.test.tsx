import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import ListingDetailPage from '@/app/studio/listings/[id]/page'
import { createFixtureApi } from '@/lib/app/fixtures'
import type { AppApi } from '@/lib/app/types'

let fx: AppApi
const publish = jest.fn()
const call = (name: keyof AppApi, args: unknown[]) => (fx[name] as (...a: unknown[]) => unknown)(...args)
jest.mock('@/lib/app/client', () => ({
  api: new Proxy({}, {
    get: (_t, name: string) => (...a: unknown[]) => {
      if (name === 'publishListing') publish(...a)
      return call(name as keyof AppApi, a)
    },
  }),
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
jest.mock('@/lib/app/session', () => ({ getSiteUrl: () => 'https://example.test/agent/amit' }))
jest.mock('@/components/app/SellersCard', () => ({ SellersCard: () => null }))
let routeId = 'l1'
let routeTab = ''
jest.mock('next/navigation', () => ({ useParams: () => ({ id: routeId }), useSearchParams: () => new URLSearchParams(routeTab ? { tab: routeTab } : {}) }))

beforeEach(() => {
  fx = createFixtureApi({ getItem: () => null, setItem: () => undefined })
  routeId = 'l1'
  routeTab = ''
  publish.mockReset()
})

describe('Listing overview', () => {
  it('opens on Overview with the price, the facts and this listing\'s numbers', async () => {
    render(<ListingDetailPage />)
    expect(await screen.findByTestId('overview-price')).toHaveTextContent('₹85 L')
    expect(screen.getByText('2 BHK · 850 sq ft · Baner, Pune · Ready to move')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('aria-current', 'page')
    await waitFor(() => expect(screen.getByTestId('overview-numbers')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Mark sold' })).toBeInTheDocument()
  })

  it('a complete draft publishes from the overview after a confirm', async () => {
    routeId = 'l2'
    render(<ListingDetailPage />)
    const box = await screen.findByRole('region', { name: 'Publish' })
    fireEvent.click(within(box).getByRole('button', { name: 'Publish' }))
    const sheet = screen.getByRole('dialog', { name: 'Publish 3 BHK in Wakad?' })
    fireEvent.click(within(sheet).getByRole('button', { name: 'Publish' }))
    await waitFor(() => expect(publish).toHaveBeenCalledWith('l2'))
    expect(await screen.findByText('Your listing is live')).toBeInTheDocument()
  })

  it('a draft missing fields says which, and sends the agent to fill them in', async () => {
    routeId = 'l2'
    jest.spyOn(fx, 'getListing').mockImplementation(async (id) => ({ ...(await createFixtureApi({ getItem: () => null, setItem: () => undefined }).getListing(id)), price_inr: 0 }))
    render(<ListingDetailPage />)
    const box = await screen.findByRole('region', { name: 'Publish' })
    expect(within(box).getByTestId('readiness')).toHaveTextContent(/To publish, add: .*price/i)
    expect(within(box).getByRole('link', { name: 'Fill in what is missing' })).toHaveAttribute('href', '/studio/listings/l2?tab=details')
    expect(within(box).queryByRole('button', { name: 'Publish' })).toBeNull()
  })

  it('the old ?tab=status link lands on Overview', async () => {
    routeTab = 'status'
    render(<ListingDetailPage />)
    expect(await screen.findByTestId('overview-price')).toBeInTheDocument()
  })
})
