import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import EnquiryForm from '@/components/site/EnquiryForm'
import DescriptionSwitch from '@/components/site/DescriptionSwitch'
import { filterListings } from '@/components/site/ListingBrowser'
import { FIXTURE_LISTINGS } from '@/lib/site/fixtures'

describe('EnquiryForm', () => {
  const props = { agentSlug: 'priya', agentName: 'Priya', agentPhone: '9876543210', waMessage: 'Hi', listingId: 'l1' }
  beforeEach(() => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: true })
  })

  it('blocks submit on invalid phone and missing consent', async () => {
    render(<EnquiryForm {...props} />)
    fireEvent.change(screen.getByLabelText('Your name'), { target: { value: 'Ravi Kumar' } })
    fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '12345' } })
    fireEvent.click(screen.getByRole('button', { name: /send enquiry/i }))
    expect(await screen.findByText(/valid 10-digit/i)).toBeInTheDocument()
    expect(screen.getByText(/tick the box/i)).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('posts inquiry with consent, listing and anon_id, then offers WhatsApp', async () => {
    render(<EnquiryForm {...props} />)
    fireEvent.change(screen.getByLabelText('Your name'), { target: { value: 'Ravi Kumar' } })
    fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '+91 98765 11111' } })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: /send enquiry/i }))
    await waitFor(() => expect(screen.getByText(/thank you, ravi/i)).toBeInTheDocument())
    const [url, init] = (global.fetch as jest.Mock).mock.calls[0]
    expect(url).toContain('/api/v1/t/inquiry')
    const body = JSON.parse(init.body)
    expect(body).toMatchObject({ agent_slug: 'priya', listing_id: 'l1', phone: '9876511111', consent: true })
    expect(body.anon_id.length).toBeGreaterThanOrEqual(8)
    expect(screen.getByRole('link', { name: /whatsapp/i })).toHaveAttribute('href', expect.stringContaining('https://wa.me/91'))
    // untouched optional block -> exactly the old payload
    for (const k of ['bhk', 'budget_min_inr', 'budget_max_inr', 'timeline', 'financing']) expect(body).not.toHaveProperty(k)
    expect(screen.queryByText(/we've noted/i)).toBeNull()
  })

  const fill = () => {
    fireEvent.change(screen.getByLabelText('Your name'), { target: { value: 'Ravi Kumar' } })
    fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '9876511111' } })
    fireEvent.click(screen.getByRole('checkbox'))
  }

  it('renders the optional block; BHK asked only off listing pages', () => {
    const { unmount } = render(<EnquiryForm {...props} agentName="Priya Sharma" />)
    expect(screen.getByText('Help Priya find the right property (optional)')).toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'BHK' })).toBeNull()
    unmount()
    render(<EnquiryForm {...props} listingId={undefined} />)
    expect(screen.getByRole('group', { name: 'BHK' })).toBeInTheDocument()
  })

  it('sends chosen fields and shows the confirmation', async () => {
    render(<EnquiryForm {...props} listingId={undefined} />)
    fill()
    fireEvent.click(screen.getByRole('button', { name: '3' }))
    fireEvent.click(screen.getByRole('button', { name: '80L-1.2Cr' }))
    fireEvent.click(screen.getByRole('button', { name: '1-3 months' }))
    fireEvent.click(screen.getByRole('button', { name: 'Home loan' }))
    fireEvent.click(screen.getByRole('button', { name: /send enquiry/i }))
    await waitFor(() => expect(screen.getByText(/thank you, ravi/i)).toBeInTheDocument())
    const body = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)
    expect(body).toMatchObject({ bhk: 3, budget_min_inr: 8_000_000, budget_max_inr: 12_000_000, timeline: '1_3_months', financing: 'home_loan' })
    expect(screen.getByText(/noted your budget and timeline/i)).toBeInTheDocument()
  })

  it('tapping a chip again clears it and open-ended budget sends null max', async () => {
    render(<EnquiryForm {...props} />)
    fill()
    const chip = screen.getByRole('button', { name: 'Now' })
    fireEvent.click(chip)
    expect(chip).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(chip)
    expect(chip).toHaveAttribute('aria-pressed', 'false')
    fireEvent.click(screen.getByRole('button', { name: '2Cr+' }))
    fireEvent.click(screen.getByRole('button', { name: /send enquiry/i }))
    await waitFor(() => expect(global.fetch).toHaveBeenCalled())
    const body = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)
    expect(body.budget_max_inr).toBeNull()
    expect(body.budget_min_inr).toBe(20_000_000)
    expect(body).not.toHaveProperty('timeline')
  })

  it('still requires consent even with chips chosen', async () => {
    render(<EnquiryForm {...props} />)
    fireEvent.change(screen.getByLabelText('Your name'), { target: { value: 'Ravi Kumar' } })
    fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '9876511111' } })
    fireEvent.click(screen.getByRole('button', { name: 'Own funds' }))
    fireEvent.click(screen.getByRole('button', { name: /send enquiry/i }))
    expect(await screen.findByText(/tick the box/i)).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })
})

describe('DescriptionSwitch', () => {
  it('shows only languages present and switches', () => {
    render(<DescriptionSwitch description={{ en: 'English text', mr: 'मराठी मजकूर' }} />)
    expect(screen.queryByRole('button', { name: 'हिन्दी' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'मराठी' }))
    expect(screen.getByText('मराठी मजकूर')).toBeInTheDocument()
  })
})

describe('filterListings', () => {
  it('filters buy/rent and BHK', () => {
    expect(filterListings(FIXTURE_LISTINGS, 'rent', 'all').every((l) => l.transaction === 'rent')).toBe(true)
    expect(filterListings(FIXTURE_LISTINGS, 'all', 2).map((l) => Math.floor(l.bhk as number))).toEqual(expect.arrayContaining([2]))
    expect(filterListings(FIXTURE_LISTINGS, 'all', 4).length).toBe(1)
  })
})
