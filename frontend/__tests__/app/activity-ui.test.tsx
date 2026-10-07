import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import ListingActivityPage from '@/app/studio/listings/[id]/activity/page'
import { ListingActivityView, ViewsChart } from '@/components/app/ListingActivityView'
import { ListingCard } from '@/components/app/ListingCard'
import { createFixtureApi } from '@/lib/app/fixtures'
import type { AppApi, ListingActivity } from '@/lib/app/types'

const getListingActivity = jest.fn()
jest.mock('@/lib/app/client', () => ({
  api: { getListingActivity: (...a: unknown[]) => getListingActivity(...a) },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
jest.mock('@/lib/app/session', () => ({ getSiteUrl: () => 'https://example.test/agent/amit' }))
jest.mock('next/navigation', () => ({ useParams: () => ({ id: 'l1' }) }))

const NOW = Date.now()
const ago = (min: number) => new Date(NOW - min * 60_000).toISOString()
const dates = Array.from({ length: 14 }, (_, i) => `2026-10-${String(i + 1).padStart(2, '0')}`)

function sample(over: Partial<ListingActivity> = {}): ListingActivity {
  return {
    listing: { id: 'l1', title: '2 BHK in Baner', status: 'live', price_inr: 8_500_000 },
    totals: { views: 47, unique_visitors: 31, enquiries: 3, qualified: 2, site_visits: 1, deals: 1, whatsapp_clicks: 6, call_clicks: 2, shares: 4 },
    by_source: { whatsapp: { views: 25, enquiries: 2 }, instagram: { views: 15, enquiries: 1 }, direct: { views: 7, enquiries: 0 } },
    daily: dates.map((date, i) => ({ date, views: i === 9 ? 9 : i % 3, enquiries: i === 9 ? 2 : i === 12 ? 1 : 0 })),
    feed: [
      { ts: ago(3), type: 'enquiry', who: { kind: 'lead', label: 'Priya Sharma', lead_id: 'c9' }, source: 'whatsapp', text: 'Priya Sharma sent an enquiry' },
      { ts: ago(120), type: 'view', who: { kind: 'visitor', label: 'Visitor 2' }, source: 'instagram', text: 'Visitor 2 viewed this from Instagram' },
      { ts: ago(60 * 30), type: 'whatsapp_click', who: { kind: 'visitor', label: 'Visitor 1' }, source: null, text: 'Visitor 1 tapped WhatsApp' },
    ],
    people: [
      { lead_id: 'c9', name: 'Priya Sharma', temperature: 'hot', score: 88, requirement_line: '2 BHK · 80L-90L · Baner', last_activity_at: ago(3) },
      { lead_id: 'c2', name: 'Amit Kulkarni', temperature: 'warm', score: 40, requirement_line: null, last_activity_at: ago(60 * 50) },
    ],
    ...over,
  }
}

beforeEach(() => getListingActivity.mockReset())

describe('Listing activity screen', () => {
  it('asks for the activity of the route id and shows the header with title, price and status', async () => {
    getListingActivity.mockResolvedValue(sample())
    render(<ListingActivityPage />)
    expect(await screen.findByRole('heading', { level: 1, name: '2 BHK in Baner' })).toBeInTheDocument()
    expect(getListingActivity).toHaveBeenCalledWith('l1', 50)
    expect(screen.getByText('₹85 L')).toBeInTheDocument()
    expect(screen.getByText('On sale')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', '/studio/listings/l1')
  })

  it('shows the six main tiles and the secondary row', async () => {
    getListingActivity.mockResolvedValue(sample())
    render(<ListingActivityView id="l1" />)
    await screen.findByTestId('activity-totals')
    const expected: Record<string, [string, string]> = {
      views: ['47', 'Views'], unique_visitors: ['31', 'Visitors'], enquiries: ['3', 'Enquiries'],
      qualified: ['2', 'Qualified'], site_visits: ['1', 'Site visits'], deals: ['1', 'Deals'],
      whatsapp_clicks: ['6', 'WhatsApp taps'], call_clicks: ['2', 'Calls'], shares: ['4', 'Shares'],
    }
    for (const [key, [n, label]] of Object.entries(expected)) {
      const tile = within(screen.getByTestId(`tile-${key}`))
      expect(tile.getByText(n)).toBeInTheDocument()
      expect(tile.getByText(label)).toBeInTheDocument()
    }
    expect(within(screen.getByTestId('activity-totals')).getAllByRole('listitem')).toHaveLength(6)
    expect(within(screen.getByTestId('activity-secondary')).getAllByRole('listitem')).toHaveLength(3)
  })

  it('draws 14 bars with enquiry dots, dates on the axis and a text summary for screen readers', async () => {
    getListingActivity.mockResolvedValue(sample())
    render(<ListingActivityView id="l1" />)
    const chart = await screen.findByTestId('activity-chart')
    const summary = 'Last 14 days: 22 views and 3 enquiries. Busiest day: 10 Oct with 9 views.'
    expect(within(chart).getByTestId('chart-summary')).toHaveTextContent(summary)
    expect(within(chart).getByRole('img', { name: summary })).toBeInTheDocument()
    const bars = within(chart).getAllByTestId('chart-bar')
    expect(bars).toHaveLength(14)
    expect(bars[9]).toHaveAttribute('data-views', '9')
    expect(bars[9]).toHaveAttribute('data-enquiries', '2')
    // enquiry markers only on days that had enquiries (2 of them)
    expect(chart.querySelectorAll('circle')).toHaveLength(2)
    expect(within(chart).getByTestId('chart-axis')).toHaveTextContent('1 Oct')
    expect(within(chart).getByTestId('chart-axis')).toHaveTextContent('14 Oct')
    expect(within(chart).getByText('Enquiries')).toBeInTheDocument()
    // the tallest bar is the busiest day, drawn taller than the others
    const heights = bars.map((b) => Number(b.querySelector('rect')?.getAttribute('height') ?? 0))
    expect(Math.max(...heights)).toBe(heights[9])
  })

  it('lists where they came from, most views first, with views and enquiries', async () => {
    getListingActivity.mockResolvedValue(sample())
    render(<ListingActivityView id="l1" />)
    const region = within(await screen.findByRole('region', { name: 'Where they came from' }))
    const rows = region.getAllByRole('listitem')
    expect(rows.map((r) => r.textContent)).toEqual([
      'WhatsApp25 views · 2 enquiries',
      'Instagram15 views · 1 enquiry',
      'Direct7 views · 0 enquiries',
    ])
  })

  it('lists interested people hottest first; tapping one opens the lead', async () => {
    getListingActivity.mockResolvedValue(sample())
    render(<ListingActivityView id="l1" />)
    const region = within(await screen.findByRole('region', { name: 'Interested people' }))
    const links = region.getAllByRole('link')
    expect(links.map((a) => a.getAttribute('href'))).toEqual(['/studio/leads/c9', '/studio/leads/c2'])
    expect(links[0]).toHaveTextContent('Priya Sharma')
    expect(links[0]).toHaveTextContent('2 BHK · 80L-90L · Baner')
    expect(links[0]).toHaveTextContent('Hot 88')
    expect(links[0]).toHaveTextContent('3m ago')
    expect(links[1]).toHaveTextContent('Warm 40')
    expect(links[1]).toHaveTextContent('2d ago')
  })

  it('shows the recent feed in the order given, in plain language, with relative times', async () => {
    getListingActivity.mockResolvedValue(sample())
    render(<ListingActivityView id="l1" />)
    const region = within(await screen.findByRole('region', { name: 'Recent activity' }))
    const items = region.getAllByTestId('feed-item')
    expect(items).toHaveLength(3)
    expect(items[0]).toHaveTextContent('Priya Sharma sent an enquiry')
    expect(items[0]).toHaveTextContent('WhatsApp · 3m ago')
    expect(items[1]).toHaveTextContent('Visitor 2 viewed this from Instagram')
    expect(items[1]).toHaveTextContent('Instagram · 2h ago')
    expect(items[2]).toHaveTextContent('Visitor 1 tapped WhatsApp')
    expect(items[2]).toHaveTextContent('Yesterday')
    // a named buyer opens the lead; an anonymous visitor is not a link
    expect(within(items[0]).getByRole('link')).toHaveAttribute('href', '/studio/leads/c9')
    expect(within(items[1]).queryByRole('link')).toBeNull()
    expect(items[1]).toHaveAttribute('data-type', 'view')
  })

  it('an empty listing leads with "share the link" and friendly notes instead of blank lists', async () => {
    getListingActivity.mockResolvedValue(
      sample({
        totals: { views: 0, unique_visitors: 0, enquiries: 0, qualified: 0, site_visits: 0, deals: 0, whatsapp_clicks: 0, call_clicks: 0, shares: 0 },
        by_source: {}, feed: [], people: [], daily: dates.map((date) => ({ date, views: 0, enquiries: 0 })),
      }),
    )
    render(<ListingActivityView id="l1" />)
    const empty = within(await screen.findByTestId('activity-empty'))
    expect(empty.getByText('No views yet')).toBeInTheDocument()
    expect(empty.getByRole('link', { name: 'Share on WhatsApp' }).getAttribute('href')).toContain(
      encodeURIComponent('https://example.test/agent/amit/listings/l1?src=whatsapp'),
    )
    expect(screen.getByText('Nobody has enquired about this listing yet.')).toBeInTheDocument()
    expect(screen.getByText('Nothing has happened on this listing yet.')).toBeInTheDocument()
    expect(screen.getByText(/where your buyers come from/)).toBeInTheDocument()
    expect(screen.queryByTestId('activity-chart')).toBeNull()
    expect(screen.getByTestId('tile-views')).toHaveTextContent('0')
  })

  it('tolerates a backend that leaves out optional lists', async () => {
    const partial = sample() as unknown as Record<string, unknown>
    delete partial.people
    delete partial.feed
    getListingActivity.mockResolvedValue(partial)
    render(<ListingActivityView id="l1" />)
    expect(await screen.findByText('Nobody has enquired about this listing yet.')).toBeInTheDocument()
  })

  it('shows an error with retry when the API fails, and retries', async () => {
    getListingActivity.mockRejectedValueOnce(new Error('Cannot reach the server')).mockResolvedValueOnce(sample())
    render(<ListingActivityView id="l1" />)
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Cannot reach the server')
    fireEvent.click(within(alert).getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { level: 1, name: '2 BHK in Baner' })).toBeInTheDocument()
    await waitFor(() => expect(getListingActivity).toHaveBeenCalledTimes(2))
  })

  it('renders the chart alone for a flat series without dots or NaN', () => {
    const { container } = render(<ViewsChart daily={dates.map((date) => ({ date, views: 0, enquiries: 0 }))} />)
    expect(container.querySelectorAll('rect')).toHaveLength(0)
    expect(container.querySelectorAll('circle')).toHaveLength(0)
    expect(screen.getByTestId('chart-summary')).toHaveTextContent('No views in the last 14 days.')
    expect(container.innerHTML).not.toContain('NaN')
  })
})

describe('Activity entry points', () => {
  let fx: AppApi
  beforeEach(() => {
    fx = createFixtureApi({ getItem: () => null, setItem: () => undefined })
  })

  it('a listing card has an Activity button next to (not inside) the card link', async () => {
    const listing = await fx.getListing('l1')
    render(<ListingCard listing={listing} />)
    const activity = screen.getByRole('link', { name: 'Activity: 2 BHK in Baner' })
    expect(activity).toHaveAttribute('href', '/studio/listings/l1/activity')
    expect(screen.getAllByRole('link')).toHaveLength(2) // the card itself and Activity
    expect(activity.closest('a')).toBe(activity) // no nested anchors
    expect(activity.parentElement?.closest('a')).toBeNull()
  })

  it('a draft listing has no Activity button', async () => {
    render(<ListingCard listing={await fx.getListing('l2')} />)
    expect(screen.queryByRole('link', { name: /Activity/ })).toBeNull()
  })
})
