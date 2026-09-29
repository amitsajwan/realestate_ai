import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import ListingDetailPage from '@/app/studio/listings/[id]/page'
import ListingsPage from '@/app/studio/listings/page'
import { BusinessToday } from '@/components/app/BusinessToday'
import { FreshnessSection } from '@/components/app/FreshnessPrompt'
import { ListingCard } from '@/components/app/ListingCard'
import { createFixtureApi } from '@/lib/app/fixtures'
import type { AppApi, BusinessToday as Today, Listing } from '@/lib/app/types'

let fx: AppApi
const spy = { confirmAvailable: jest.fn(), setListingStatus: jest.fn(), updateListing: jest.fn(), listListings: jest.fn() }
const getToday = jest.fn()
const call = (name: keyof AppApi, args: unknown[]) => (fx[name] as (...a: unknown[]) => unknown)(...args)
jest.mock('@/lib/app/client', () => ({
  api: {
    listListings: (...a: unknown[]) => { spy.listListings(...a); return call('listListings', a) },
    getListing: (...a: unknown[]) => call('getListing', a),
    getPerformance: (...a: unknown[]) => call('getPerformance', a),
    listLeads: (...a: unknown[]) => call('listLeads', a),
    getToday: (...a: unknown[]) => getToday(...a),
    confirmAvailable: (...a: unknown[]) => { spy.confirmAvailable(...a); return call('confirmAvailable', a) },
    setListingStatus: (...a: unknown[]) => { spy.setListingStatus(...a); return call('setListingStatus', a) },
    updateListing: (...a: unknown[]) => { spy.updateListing(...a); return call('updateListing', a) },
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
jest.mock('@/lib/app/session', () => ({
  useSession: () => ({ siteUrl: null, logout: jest.fn() }),
  getSiteUrl: () => 'https://example.test/agent/amit',
}))
let routeId = 'l4'
jest.mock('next/navigation', () => ({ useParams: () => ({ id: routeId }), useSearchParams: () => new URLSearchParams() }))

beforeEach(() => {
  fx = createFixtureApi({ getItem: () => null, setItem: () => undefined })
  Object.values(spy).forEach((m) => m.mockClear())
  getToday.mockReset()
  routeId = 'l4'
})

const prompt = (id: string) => within(screen.getByTestId(`freshness-${id}`))

describe('Freshness prompts on the Listings screen', () => {
  it('asks "Is this still available?" for a confirm listing and shows the red hidden state for a hidden one', async () => {
    render(<ListingsPage />)
    const ask = await screen.findByTestId('freshness-l3')
    expect(ask).toHaveAttribute('data-state', 'confirm')
    expect(ask.className).toMatch(/amber/)
    expect(prompt('l3').getByText('Is this still available?')).toBeInTheDocument()
    expect(ask).toHaveTextContent('2 BHK near Baner Road')
    expect(ask).toHaveTextContent('Last confirmed 30 days ago')

    const hidden = screen.getByTestId('freshness-l4')
    expect(hidden).toHaveAttribute('data-state', 'hidden')
    expect(hidden.className).toMatch(/red/)
    expect(prompt('l4').getByText('Hidden from buyers until you confirm')).toBeInTheDocument()
    expect(prompt('l4').queryByText('Is this still available?')).toBeNull()
    expect(hidden).toHaveTextContent('Last confirmed 52 days ago')
    // both have the same three big buttons
    for (const id of ['l3', 'l4']) {
      expect(prompt(id).getByRole('button', { name: 'Yes, still available' })).toBeInTheDocument()
      expect(prompt(id).getByRole('button', { name: 'It is sold' })).toBeInTheDocument()
      expect(prompt(id).getByRole('button', { name: 'Pause it' })).toBeInTheDocument()
    }
    // hidden listing comes first, and fresh listings get no card
    const order = screen.getAllByTestId(/^freshness-l/).map((e) => e.getAttribute('data-testid'))
    expect(order).toEqual(['freshness-l4', 'freshness-l3'])
    expect(screen.queryByTestId('freshness-l1')).toBeNull()
  })

  it('listing cards show a Confirm or Hidden chip only when needed', async () => {
    render(<ListingsPage />)
    await screen.findByTestId('freshness-l3')
    const chips = screen.getAllByTestId('freshness-chip').map((c) => c.textContent)
    expect(chips.sort()).toEqual(['Confirm', 'Hidden'])
  })

  it('"Yes, still available" confirms, and the card, chip and prompt update', async () => {
    render(<ListingsPage />)
    await screen.findByTestId('freshness-l3')
    fireEvent.click(prompt('l3').getByRole('button', { name: 'Yes, still available' }))
    await waitFor(() => expect(screen.queryByTestId('freshness-l3')).toBeNull())
    expect(spy.confirmAvailable).toHaveBeenCalledWith('l3')
    expect(spy.setListingStatus).not.toHaveBeenCalled()
    expect(screen.getByRole('status')).toHaveTextContent('2 BHK near Baner Road: Thanks. Buyers can see it.')
    expect(screen.getAllByTestId('freshness-chip')).toHaveLength(1) // only the hidden one is left
    expect(screen.getByTestId('freshness-l4')).toBeInTheDocument()
    expect((await fx.getListing('l3')).freshness).toBe('fresh')
  })

  it('confirming a hidden listing brings it back', async () => {
    render(<ListingsPage />)
    await screen.findByTestId('freshness-l4')
    fireEvent.click(prompt('l4').getByRole('button', { name: 'Yes, still available' }))
    await waitFor(() => expect(screen.queryByTestId('freshness-l4')).toBeNull())
    expect(spy.confirmAvailable).toHaveBeenCalledWith('l4')
    expect(screen.queryByText('Hidden from buyers until you confirm')).toBeNull()
    expect(screen.queryByText('Hidden')).toBeNull()
  })

  it('"It is sold" marks the listing sold', async () => {
    render(<ListingsPage />)
    await screen.findByTestId('freshness-l3')
    fireEvent.click(prompt('l3').getByRole('button', { name: 'It is sold' }))
    await waitFor(() => expect(screen.queryByTestId('freshness-l3')).toBeNull())
    expect(spy.setListingStatus).toHaveBeenCalledWith('l3', 'sold')
    expect(spy.confirmAvailable).not.toHaveBeenCalled()
    expect(screen.getByRole('status')).toHaveTextContent('Marked as sold.')
    expect(screen.getByText('sold')).toBeInTheDocument() // the card's status chip
  })

  it('"Pause it" pauses the listing', async () => {
    render(<ListingsPage />)
    await screen.findByTestId('freshness-l4')
    fireEvent.click(prompt('l4').getByRole('button', { name: 'Pause it' }))
    await waitFor(() => expect(screen.queryByTestId('freshness-l4')).toBeNull())
    expect(spy.setListingStatus).toHaveBeenCalledWith('l4', 'paused')
    expect(screen.getByRole('status')).toHaveTextContent('Paused. Buyers cannot see it.')
    expect(screen.getByText('paused')).toBeInTheDocument()
  })

  it('a rental says "It is rented" and marks it rented', async () => {
    await fx.updateListing('l3', { transaction: 'rent' })
    render(<ListingsPage />)
    await screen.findByTestId('freshness-l3')
    expect(prompt('l3').queryByRole('button', { name: 'It is sold' })).toBeNull()
    fireEvent.click(prompt('l3').getByRole('button', { name: 'It is rented' }))
    await waitFor(() => expect(spy.setListingStatus).toHaveBeenCalledWith('l3', 'rented'))
    expect(await screen.findByText('rented')).toBeInTheDocument()
  })

  it('disables the buttons while working and shows an error (with buttons back) when it fails', async () => {
    render(<ListingsPage />)
    await screen.findByTestId('freshness-l3')
    const failing = jest.spyOn(fx, 'confirmAvailable').mockRejectedValueOnce(new Error('Cannot reach the server'))
    fireEvent.click(prompt('l3').getByRole('button', { name: 'Yes, still available' }))
    expect(prompt('l3').getByRole('button', { name: 'It is sold' })).toBeDisabled()
    expect(await prompt('l3').findByRole('alert')).toHaveTextContent('Cannot reach the server')
    await waitFor(() => expect(prompt('l3').getByRole('button', { name: 'Yes, still available' })).toBeEnabled())
    expect(screen.getByTestId('freshness-l3')).toBeInTheDocument() // still asking
    failing.mockRestore()
  })

  it('shows nothing on an older backend that sends no freshness fields', async () => {
    const list = await fx.listListings()
    jest.spyOn(fx, 'listListings').mockResolvedValue(list.map(({ freshness, days_since_confirmed, ...rest }) => rest as Listing))
    render(<ListingsPage />)
    await screen.findByText('2 BHK in Baner')
    expect(screen.queryByText('Is this still available?')).toBeNull()
    expect(screen.queryByTestId('freshness-chip')).toBeNull()
  })

  it('does not ask about a listing that is paused or sold, whatever the server says', () => {
    const l = { id: 'x', status: 'paused', freshness: 'hidden', title: 'X' } as Listing
    const { container } = render(<FreshnessSection listings={[l]} onUpdated={() => undefined} />)
    expect(container).toBeEmptyDOMElement()
    render(<ListingCard listing={l} />)
    expect(screen.queryByTestId('freshness-chip')).toBeNull()
  })
})

describe('Freshness prompt on the listing screen', () => {
  it('shows the hidden state at the top of a hidden listing and confirming clears it', async () => {
    render(<ListingDetailPage />)
    expect(await screen.findByTestId('freshness-l4')).toHaveAttribute('data-state', 'hidden')
    expect(screen.getByRole('link', { name: 'Activity' })).toHaveAttribute('href', '/studio/listings/l4/activity')
    fireEvent.click(prompt('l4').getByRole('button', { name: 'Yes, still available' }))
    await waitFor(() => expect(screen.queryByTestId('freshness-l4')).toBeNull())
    expect(spy.confirmAvailable).toHaveBeenCalledWith('l4')
    expect(screen.getByRole('status')).toHaveTextContent('Thanks. Buyers can see it.')
  })

  it('a fresh listing has no prompt, and saving never sends the computed freshness fields', async () => {
    routeId = 'l1'
    render(<ListingDetailPage />)
    await screen.findByRole('heading', { level: 1, name: '2 BHK in Baner' })
    expect(screen.queryByTestId('freshness-l1')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(spy.updateListing).toHaveBeenCalled())
    const sent = spy.updateListing.mock.calls[0][1] as Record<string, unknown>
    expect(sent).not.toHaveProperty('freshness')
    expect(sent).not.toHaveProperty('days_since_confirmed')
  })

  it('a draft has no Activity button', async () => {
    routeId = 'l2'
    render(<ListingDetailPage />)
    await screen.findByRole('heading', { level: 1, name: '3 BHK in Wakad' })
    expect(screen.queryByRole('link', { name: 'Activity' })).toBeNull()
  })
})

describe('Home: "Listings that need your confirmation"', () => {
  const todayBase = async (): Promise<Today> => fx.getToday()

  it('adds a confirm_listing item built from the listings list, linking to the listing screen card', async () => {
    getToday.mockResolvedValue(await todayBase())
    render(<BusinessToday />)
    const card = await screen.findByTestId('action-confirm_listing')
    expect(card).toHaveTextContent('Listings that need your confirmation')
    expect(card).toHaveTextContent('2 listings need a quick check. 1 hidden from buyers until you confirm.')
    const open = within(card).getByRole('link', { name: /Confirm now/ })
    expect(open).toHaveAttribute('href', '/studio/listings#confirm')
    expect(within(card).getAllByRole('link').every((a) => a.getAttribute('href') === '/studio/listings#confirm')).toBe(true)
    // hidden listings make it priority 1: after urgent buyer calls, before the "send property" / marketing ideas
    const order = screen.getAllByTestId(/^action-/).map((e) => e.getAttribute('data-testid')!.replace('action-', ''))
    const at = order.indexOf('confirm_listing')
    expect(at).toBeGreaterThan(order.lastIndexOf('call'))
    expect(at).toBeLessThan(order.indexOf('create_marketing'))
  })

  it('a single listing needing confirmation links straight to it', async () => {
    await fx.confirmAvailable('l4')
    getToday.mockResolvedValue(await todayBase())
    render(<BusinessToday />)
    const card = await screen.findByTestId('action-confirm_listing')
    expect(card).toHaveTextContent('1 listing needs a quick check.')
    expect(within(card).getByRole('link', { name: /Confirm now/ })).toHaveAttribute('href', '/studio/listings/l3')
  })

  it('does not appear when every listing is fresh', async () => {
    await fx.confirmAvailable('l3')
    await fx.confirmAvailable('l4')
    getToday.mockResolvedValue(await todayBase())
    render(<BusinessToday />)
    await screen.findByTestId('headline')
    expect(screen.queryByTestId('action-confirm_listing')).toBeNull()
  })

  it('does not duplicate an item the backend already sent', async () => {
    const today = await todayBase()
    getToday.mockResolvedValue({
      ...today,
      actions: [{ type: 'confirm_listing', title: 'Confirm your listings', detail: 'From the server', priority: 1 }],
    })
    render(<BusinessToday />)
    expect(await screen.findByText('Confirm your listings')).toBeInTheDocument()
    expect(screen.getAllByTestId('action-confirm_listing')).toHaveLength(1)
    expect(screen.queryByText('Listings that need your confirmation')).toBeNull()
  })

  it('home still works when the listings cannot be loaded', async () => {
    getToday.mockResolvedValue(await todayBase())
    jest.spyOn(fx, 'listListings').mockRejectedValue(new Error('boom'))
    render(<BusinessToday />)
    expect(await screen.findByTestId('headline')).toBeInTheDocument()
    expect(screen.queryByTestId('action-confirm_listing')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
