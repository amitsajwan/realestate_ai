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

  it('shows the headline and hot buyers only: counts and follow-ups live on Leads, the website on My brand', async () => {
    const fx = createFixtureApi({ getItem: () => null, setItem: () => undefined })
    getToday.mockResolvedValue(await fx.getToday())
    listLeads.mockResolvedValue(await fx.listLeads())
    render(<BusinessToday />)

    expect(await screen.findByTestId('headline')).toHaveTextContent("2 buyers haven't been contacted today.")
    const hot = screen.getByRole('region', { name: 'Hot buyers' })
    expect(within(hot).getByText('Priya Nair')).toBeInTheDocument()
    expect(within(hot).getByText('2 BHK · 70L-95L · Baner · Now')).toBeInTheDocument()
    expect(within(hot).getByRole('link', { name: 'Call Priya Nair' })).toHaveAttribute('href', 'tel:+919811223344')
    expect(within(hot).getByRole('link', { name: 'WhatsApp Rohit Deshmukh' }).getAttribute('href')).toMatch(/^https:\/\/wa\.me\/919822012345\?text=/)
    expect(within(hot).getAllByText(/Best match/)).toHaveLength(2)
    expect(within(hot).getByRole('link', { name: /All leads/ })).toHaveAttribute('href', '/studio/leads?tab=all&hot=1')

    expect(screen.queryByText('New enquiries')).toBeNull()
    expect(screen.queryByRole('region', { name: 'Follow-ups due' })).toBeNull()
    expect(screen.queryByText('My website')).toBeNull()
  })

  it('shows the onboarding empty state for a brand-new agent with the add-listing button', async () => {
    getToday.mockResolvedValue(empty)
    listLeads.mockResolvedValue([])
    render(<BusinessToday />)
    expect(await screen.findByText('Get your first enquiry')).toBeInTheDocument()
    expect(screen.queryByTestId('headline')).toBeNull()
    expect(screen.getByRole('link', { name: /add listing/i })).toHaveAttribute('href', '/studio/listings/new')
  })

  it('shows an error with retry when the API fails', async () => {
    getToday.mockRejectedValue(new Error('Cannot reach the server'))
    listLeads.mockResolvedValue([])
    render(<BusinessToday />)
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Cannot reach the server'))
  })
})
