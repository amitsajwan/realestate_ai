import { render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { BusinessToday } from '@/components/app/BusinessToday'
import { createFixtureApi } from '@/lib/app/fixtures'
import type { BusinessToday as Today } from '@/lib/app/types'

const getToday = jest.fn()
const listLeads = jest.fn()
jest.mock('@/lib/app/client', () => ({
  api: { getToday: (...a: unknown[]) => getToday(...a), listLeads: (...a: unknown[]) => listLeads(...a) },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
const siteUrl = 'https://example.test/agent/amit'
jest.mock('@/lib/app/session', () => ({ useSession: () => ({ siteUrl: 'https://example.test/agent/amit', logout: jest.fn() }) }))

const empty: Today = {
  counts: { new_enquiries_24h: 0, hot: 0, site_visits: 0, follow_ups_due: 0, uncontacted: 0 },
  hot_buyers: [], follow_ups: [], headline: "You're all caught up.",
}

describe('BusinessToday', () => {
  beforeEach(() => {
    getToday.mockReset()
    listLeads.mockReset()
  })

  it('shows the headline, count tiles linking to filtered lists, hot buyers and follow-ups', async () => {
    const fx = createFixtureApi({ getItem: () => null, setItem: () => undefined })
    getToday.mockResolvedValue(await fx.getToday())
    listLeads.mockResolvedValue(await fx.listLeads())
    render(<BusinessToday />)

    expect(await screen.findByTestId('headline')).toHaveTextContent("2 buyers haven't been contacted today.")
    const tile = (label: string) => screen.getAllByText(label).map((e) => e.closest('a')).find(Boolean)!
    expect(tile('New enquiries')).toHaveAttribute('href', '/studio/leads?filter=new')
    expect(tile('Hot buyers')).toHaveAttribute('href', '/studio/leads?filter=hot')
    expect(tile('Site visits')).toHaveAttribute('href', '/studio/leads?filter=site_visit')
    expect(tile('Follow-ups due')).toHaveAttribute('href', '/studio/leads?filter=followups')
    expect(within(tile('Hot buyers')).getByText('2')).toBeInTheDocument()

    const hot = screen.getByRole('region', { name: 'Hot buyers' })
    expect(within(hot).getByText('Priya Nair')).toBeInTheDocument()
    expect(within(hot).getByText('2 BHK · 70L-95L · Baner · Now')).toBeInTheDocument()
    expect(within(hot).getByRole('link', { name: 'Call Priya Nair' })).toHaveAttribute('href', 'tel:+919811223344')
    expect(within(hot).getByRole('link', { name: 'WhatsApp Rohit Deshmukh' }).getAttribute('href')).toMatch(/^https:\/\/wa\.me\/919822012345\?text=/)
    expect(within(hot).getAllByText(/Best match/)).toHaveLength(2)

    const fu = screen.getByRole('region', { name: 'Follow-ups due' })
    const row = within(fu).getByText('Sneha Kulkarni').closest('a')!
    expect(row).toHaveAttribute('href', '/studio/leads/c2')
    expect(row).toHaveTextContent(/Overdue/)

    // leads section first, website card + add-listing below
    expect(hot.compareDocumentPosition(screen.getByText('My website')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByRole('link', { name: /add listing/i })).toBeInTheDocument()
    expect(screen.getByText(siteUrl)).toBeInTheDocument()
  })

  it('shows the onboarding empty state for a brand-new agent, site card first', async () => {
    getToday.mockResolvedValue(empty)
    listLeads.mockResolvedValue([])
    render(<BusinessToday />)
    expect(await screen.findByText('Get your first enquiry')).toBeInTheDocument()
    expect(screen.queryByTestId('headline')).toBeNull()
    expect(screen.queryByText('New enquiries')).toBeNull()
    expect(screen.getByText('My website')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /add listing/i })).toHaveAttribute('href', '/studio/listings/new')
  })

  it('shows an error with retry when the API fails', async () => {
    getToday.mockRejectedValue(new Error('Cannot reach the server'))
    listLeads.mockResolvedValue([])
    render(<BusinessToday />)
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Cannot reach the server'))
  })
})
