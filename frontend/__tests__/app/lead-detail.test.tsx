import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { LeadDetailView } from '@/components/app/LeadDetailView'
import { createFixtureApi } from '@/lib/app/fixtures'
import type { AppApi } from '@/lib/app/types'

let fx: AppApi
const spy = { updateLead: jest.fn(), createFollowupDraft: jest.fn() }
jest.mock('@/lib/app/client', () => ({
  api: {
    getLead: (id: string) => fx.getLead(id),
    listListings: () => fx.listListings(),
    updateLead: (...a: unknown[]) => { spy.updateLead(...a); return (fx.updateLead as (...x: unknown[]) => unknown)(...a) },
    createFollowupDraft: (...a: unknown[]) => { spy.createFollowupDraft(...a); return (fx.createFollowupDraft as (...x: unknown[]) => unknown)(...a) },
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))

const fresh = () => createFixtureApi({ getItem: () => null, setItem: () => undefined })

beforeEach(() => {
  fx = fresh()
  spy.updateLead.mockClear()
  spy.createFollowupDraft.mockClear()
})

describe('LeadDetailView', () => {
  it('renders summary, requirement chips, matches and follow-up sections', async () => {
    render(<LeadDetailView id="c1" />)
    const summary = await screen.findByRole('region', { name: 'AI summary' })
    expect(within(summary).getByText(/Wants a 2 BHK/)).toBeInTheDocument()
    expect(within(summary).getByRole('button', { name: 'Schedule a site visit' })).toBeInTheDocument()

    const want = screen.getByRole('region', { name: 'What they want' })
    ;['2 BHK', '₹80 L - ₹90 L', 'Baner', 'In 1-3 months', 'Home loan'].forEach((c) => expect(within(want).getByText(c)).toBeInTheDocument())
    expect(within(want).getByTestId('req-source')).toHaveTextContent('Stated by the buyer')

    const matches = screen.getByRole('region', { name: 'Matching properties' })
    const first = within(matches).getAllByRole('link')[0]
    expect(first).toHaveAttribute('href', '/studio/listings/l1')
    expect(first).toHaveTextContent('₹85 L')
    expect(first).toHaveTextContent('Inside budget')
    expect(within(first).getByRole('progressbar')).toBeInTheDocument()

    expect(screen.getByTestId('followup-line')).toHaveTextContent('No follow-up set')
  })

  it('primary next action schedules a site visit via PATCH stage', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Schedule a site visit' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c1', { stage: 'site_visit' }))
    expect(await screen.findByRole('button', { name: 'Site visit', pressed: true })).toBeInTheDocument()
  })

  it('a call next action is a tel: link, and empty requirement/matches show plain messages', async () => {
    render(<LeadDetailView id="c3" />)
    const summary = await screen.findByRole('region', { name: 'AI summary' })
    expect(within(summary).getByRole('link', { name: 'Call now' })).toHaveAttribute('href', 'tel:+919767654321')
    expect(screen.getByText('They have not shared what they want yet.')).toBeInTheDocument()
    expect(screen.getByText('No matching listings yet.')).toBeInTheDocument()
  })

  it('quick follow-up buttons PATCH follow_up_at', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Tomorrow' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c1', { follow_up_at: expect.stringMatching(/^\d{4}-\d\d-\d\dT/) }))
    await waitFor(() => expect(screen.getByTestId('followup-line')).toHaveTextContent(/^Due /))
  })

  it('draft flow: shows reasons, edits text, encodes the wa.me url, switches language, never auto-sends', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Draft follow-up' }))
    const box = (await screen.findByLabelText('Your message')) as HTMLTextAreaElement
    expect(spy.createFollowupDraft).toHaveBeenCalledWith('c1', 'en')
    expect(box.value).toContain('Rohit')
    expect(screen.getByText('Why this message')).toBeInTheDocument()
    expect(screen.getByText(/Budget 80L-90L/)).toBeInTheDocument()
    expect(screen.getByText(/never send anything for you/i)).toBeInTheDocument()

    fireEvent.change(box, { target: { value: 'Hello Rohit & family, 2 BHK at 85L?' } })
    const send = screen.getByRole('link', { name: 'Send on WhatsApp' })
    expect(send).toHaveAttribute('href', `https://wa.me/919822012345?text=${encodeURIComponent('Hello Rohit & family, 2 BHK at 85L?')}`)
    expect(send).toHaveAttribute('target', '_blank')

    fireEvent.click(screen.getByRole('button', { name: 'MR' }))
    await waitFor(() => expect(spy.createFollowupDraft).toHaveBeenLastCalledWith('c1', 'mr'))
    expect(await screen.findByText(/not ready yet, so the message is in English/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'HI' }))
    await waitFor(() => expect((screen.getByLabelText('Your message') as HTMLTextAreaElement).value).toContain('नमस्ते'))
  })

  it('follow up next action opens the draft (site_visit stage lead)', async () => {
    render(<LeadDetailView id="c4" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Follow up' }))
    expect(await screen.findByLabelText('Your message')).toBeInTheDocument()
  })
})
