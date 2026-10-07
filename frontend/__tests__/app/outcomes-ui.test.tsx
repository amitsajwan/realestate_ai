import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { BusinessToday, ResultsCard } from '@/components/app/BusinessToday'
import { LeadDetailView } from '@/components/app/LeadDetailView'
import { ListingCard } from '@/components/app/ListingCard'
import { OutcomeBadge } from '@/components/app/OutcomeSheets'
import LeadsPage from '@/app/studio/leads/page'
import { createFixtureApi } from '@/lib/app/fixtures'
import type { AppApi, BusinessToday as Today, TodayResults } from '@/lib/app/types'

let fx: AppApi
const spy = { updateLead: jest.fn(), setListingStatus: jest.fn() }
const getToday = jest.fn()
jest.mock('@/lib/app/client', () => ({
  api: {
    getLead: (id: string) => fx.getLead(id),
    listListings: () => fx.listListings(),
    listLeads: (...a: unknown[]) => (fx.listLeads as (...x: unknown[]) => unknown)(...a),
    getToday: (...a: unknown[]) => getToday(...a),
    updateLead: (...a: unknown[]) => { spy.updateLead(...a); return (fx.updateLead as (...x: unknown[]) => unknown)(...a) },
    setListingStatus: (...a: unknown[]) => { spy.setListingStatus(...a); return (fx.setListingStatus as (...x: unknown[]) => unknown)(...a) },
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
jest.mock('@/lib/app/session', () => ({ useSession: () => ({ siteUrl: null, logout: jest.fn() }) }))
jest.mock('next/navigation', () => ({ useSearchParams: () => new URLSearchParams() }))

beforeEach(() => {
  fx = createFixtureApi({ getItem: () => null, setItem: () => undefined })
  spy.updateLead.mockClear()
  spy.setListingStatus.mockClear()
  getToday.mockReset()
})

const stagePill = (name: string) => screen.getByRole('button', { name })
const dialog = (name: string) => screen.findByRole('dialog', { name })

describe('Deal closed sheet (stage Won)', () => {
  it('opens on Won, pre-filled from the enquired listing, both fields editable', async () => {
    render(<LeadDetailView id="c1" />)
    await screen.findByRole('region', { name: 'AI summary' })
    fireEvent.click(stagePill('Won'))
    const sheet = within(await dialog('Deal closed'))
    expect(spy.updateLead).not.toHaveBeenCalled() // nothing changes until Save
    expect(sheet.getByLabelText('Deal price')).toHaveValue('85 L')
    expect(sheet.getByLabelText('Which property?')).toHaveValue('l1')
    // the picker offers live listings, not drafts
    const options = within(sheet.getByLabelText('Which property?')).getAllByRole('option').map((o) => o.textContent)
    expect(options).toEqual(expect.arrayContaining(['2 BHK in Baner', '3 BHK in Kharadi']))
    expect(options).not.toContain('3 BHK in Wakad')
  })

  it('Save sends the pre-filled price and listing', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    fireEvent.click(within(await dialog('Deal closed')).getByRole('button', { name: 'Save' }))
    await waitFor(() =>
      expect(spy.updateLead).toHaveBeenCalledWith('c1', { stage: 'won', outcome: { deal_price_inr: 8_500_000, listing_id: 'l1' } }),
    )
    expect(await screen.findByRole('button', { name: 'Won', pressed: true })).toBeInTheDocument()
  })

  it('parses lakh and crore the agent types, and shows what it understood', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    const sheet = within(await dialog('Deal closed'))
    const price = sheet.getByLabelText('Deal price')
    fireEvent.change(price, { target: { value: '82.5 lakh' } })
    expect(sheet.getByTestId('deal-price-preview')).toHaveTextContent('= ₹82.5 L')
    fireEvent.click(sheet.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c1', { stage: 'won', outcome: { deal_price_inr: 8_250_000, listing_id: 'l1' } }))
  })

  it('accepts a crore amount and a bare rupee amount', async () => {
    render(<LeadDetailView id="c2" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    const sheet = within(await dialog('Deal closed'))
    expect(sheet.getByLabelText('Deal price')).toHaveValue('1.4 Cr') // l4 is 1.4 Cr
    fireEvent.change(sheet.getByLabelText('Deal price'), { target: { value: '₹1,35,00,000' } })
    fireEvent.click(sheet.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c2', { stage: 'won', outcome: { deal_price_inr: 13_500_000, listing_id: 'l4' } }))
  })

  it('does not save a price it cannot read, and says so', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    const sheet = within(await dialog('Deal closed'))
    fireEvent.change(sheet.getByLabelText('Deal price'), { target: { value: 'about eighty' } })
    fireEvent.click(sheet.getByRole('button', { name: 'Save' }))
    expect(await sheet.findByRole('alert')).toHaveTextContent('Enter an amount like 85 lakh')
    expect(spy.updateLead).not.toHaveBeenCalled()
    fireEvent.change(sheet.getByLabelText('Deal price'), { target: { value: '0' } })
    fireEvent.click(sheet.getByRole('button', { name: 'Save' }))
    expect(await sheet.findByRole('alert')).toBeInTheDocument()
    expect(spy.updateLead).not.toHaveBeenCalled()
  })

  it('price and property are optional: both empty saves just the stage', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    const sheet = within(await dialog('Deal closed'))
    fireEvent.change(sheet.getByLabelText('Which property?'), { target: { value: '' } })
    fireEvent.change(sheet.getByLabelText('Deal price'), { target: { value: '' } })
    fireEvent.click(sheet.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c1', { stage: 'won' }))
    expect(screen.queryByRole('dialog')).toBeNull() // no listing, so no mark-sold question
  })

  it('a price with no property is sent alone', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    const sheet = within(await dialog('Deal closed'))
    fireEvent.change(sheet.getByLabelText('Which property?'), { target: { value: '' } })
    fireEvent.change(sheet.getByLabelText('Deal price'), { target: { value: '80 lakh' } })
    fireEvent.click(sheet.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c1', { stage: 'won', outcome: { deal_price_inr: 8_000_000 } }))
  })

  it('changing the property re-fills the price until the agent types their own', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    const sheet = within(await dialog('Deal closed'))
    fireEvent.change(sheet.getByLabelText('Which property?'), { target: { value: 'l3' } })
    expect(sheet.getByLabelText('Deal price')).toHaveValue('92 L')
    fireEvent.change(sheet.getByLabelText('Deal price'), { target: { value: '90 lakh' } })
    fireEvent.change(sheet.getByLabelText('Which property?'), { target: { value: 'l4' } })
    expect(sheet.getByLabelText('Deal price')).toHaveValue('90 lakh')
  })

  it('dismissing (backdrop, Escape) does not change the stage', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    await dialog('Deal closed')
    fireEvent.click(screen.getByTestId('sheet-backdrop'))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.getByRole('button', { name: 'New', pressed: true })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Won', pressed: false })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Won' }))
    await dialog('Deal closed')
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(spy.updateLead).not.toHaveBeenCalled()
    expect((await fx.getLead('c1')).stage).toBe('new')
  })

  it('a failed save keeps the sheet open with the message', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    const sheet = await dialog('Deal closed')
    const orig = fx.updateLead
    fx.updateLead = () => Promise.reject(new Error('Cannot reach the server'))
    fireEvent.click(within(sheet).getByRole('button', { name: 'Save' }))
    expect(await within(sheet).findByRole('alert')).toHaveTextContent('Cannot reach the server')
    expect(screen.getByRole('dialog', { name: 'Deal closed' })).toBeInTheDocument()
    fx.updateLead = orig
  })
})

describe('Why was it lost? sheet (stage Lost)', () => {
  it('shows the reason chips and a Skip option', async () => {
    render(<LeadDetailView id="c3" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Lost' }))
    const sheet = within(await dialog('Why was it lost?'))
    ;['Price', 'Bought elsewhere', 'Not responding', 'Changed mind', 'Other', 'Skip'].forEach((n) =>
      expect(sheet.getByRole('button', { name: n })).toBeInTheDocument(),
    )
    expect(spy.updateLead).not.toHaveBeenCalled()
  })

  it('tapping a reason saves stage lost with that reason', async () => {
    render(<LeadDetailView id="c3" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Lost' }))
    fireEvent.click(within(await dialog('Why was it lost?')).getByRole('button', { name: 'Bought elsewhere' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c3', { stage: 'lost', outcome: { lost_reason: 'bought_elsewhere' } }))
    expect(await screen.findByRole('button', { name: 'Lost', pressed: true })).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('Skip saves stage lost with no outcome', async () => {
    render(<LeadDetailView id="c3" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Lost' }))
    fireEvent.click(within(await dialog('Why was it lost?')).getByRole('button', { name: 'Skip' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c3', { stage: 'lost' }))
    expect(await screen.findByTestId('outcome-summary')).toHaveTextContent('Lost')
  })

  it('dismissing does not change the stage', async () => {
    render(<LeadDetailView id="c3" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Lost' }))
    await dialog('Why was it lost?')
    fireEvent.click(screen.getByTestId('sheet-backdrop'))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(spy.updateLead).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'New', pressed: true })).toBeInTheDocument()
  })
})

describe('Mark the listing as sold?', () => {
  async function wonWithListing() {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    fireEvent.click(within(await dialog('Deal closed')).getByRole('button', { name: 'Save' }))
    return dialog('Mark 2 BHK in Baner as sold?')
  }

  it('asks after Won; Yes calls the existing listing status endpoint', async () => {
    const prompt = within(await wonWithListing())
    expect(spy.setListingStatus).not.toHaveBeenCalled()
    fireEvent.click(prompt.getByRole('button', { name: 'Yes' }))
    await waitFor(() => expect(spy.setListingStatus).toHaveBeenCalledWith('l1', 'sold'))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect((await fx.getListing('l1')).status).toBe('sold')
  })

  it('Not now leaves the listing alone', async () => {
    const prompt = within(await wonWithListing())
    fireEvent.click(prompt.getByRole('button', { name: 'Not now' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(spy.setListingStatus).not.toHaveBeenCalled()
    expect((await fx.getListing('l1')).status).toBe('live')
  })

  it('says rented for a rent listing', async () => {
    const rent = await fx.createListing({ title: 'Flat for rent', transaction: 'rent', price_inr: 30_000 })
    await fx.setListingStatus(rent.id, 'live')
    render(<LeadDetailView id="c3" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    const sheet = within(await dialog('Deal closed'))
    fireEvent.change(sheet.getByLabelText('Which property?'), { target: { value: rent.id } })
    fireEvent.click(sheet.getByRole('button', { name: 'Save' }))
    fireEvent.click(within(await dialog('Mark Flat for rent as rented?')).getByRole('button', { name: 'Yes' }))
    await waitFor(() => expect(spy.setListingStatus).toHaveBeenCalledWith(rent.id, 'rented'))
  })

  it('does not ask when the listing is already sold', async () => {
    await fx.setListingStatus('l1', 'sold')
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    fireEvent.click(within(await dialog('Deal closed')).getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalled())
    await screen.findByTestId('outcome-summary')
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('shows the message when marking fails, and stays open', async () => {
    const prompt = await wonWithListing()
    const orig = fx.setListingStatus
    fx.setListingStatus = () => Promise.reject(new Error('Listing not found'))
    fireEvent.click(within(prompt).getByRole('button', { name: 'Yes' }))
    expect(await within(prompt).findByRole('alert')).toHaveTextContent('Listing not found')
    fx.setListingStatus = orig
  })
})

describe('outcome summary card and undo', () => {
  it('shows Won with price and property, and Reopen moves the lead back to Contacted', async () => {
    render(<LeadDetailView id="c1" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Won' }))
    fireEvent.click(within(await dialog('Deal closed')).getByRole('button', { name: 'Save' }))
    fireEvent.click(within(await dialog('Mark 2 BHK in Baner as sold?')).getByRole('button', { name: 'Not now' }))
    const card = await screen.findByTestId('outcome-summary')
    expect(card).toHaveTextContent('Won: ₹85 L on the 2 BHK in Baner')

    fireEvent.click(within(card).getByRole('button', { name: 'Reopen' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenLastCalledWith('c1', { stage: 'contacted' }))
    await waitFor(() => expect(screen.queryByTestId('outcome-summary')).toBeNull())
    expect(screen.getByRole('button', { name: 'Contacted', pressed: true })).toBeInTheDocument()
    expect((await fx.getLead('c1')).outcome).toBeNull()
  })

  it('shows Lost with the reason for a lead that was already lost', async () => {
    await fx.updateLead('c3', { stage: 'lost', outcome: { lost_reason: 'bought_elsewhere' } })
    render(<LeadDetailView id="c3" />)
    expect(await screen.findByTestId('outcome-summary')).toHaveTextContent('Lost: bought elsewhere')
  })

  it('no card for an open lead', async () => {
    render(<LeadDetailView id="c1" />)
    await screen.findByRole('region', { name: 'AI summary' })
    expect(screen.queryByTestId('outcome-summary')).toBeNull()
  })

  it('saving a note on a won lead does not touch its outcome', async () => {
    await fx.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_500_000, listing_id: 'l1' } })
    render(<LeadDetailView id="c1" />)
    await screen.findByTestId('outcome-summary')
    fireEvent.change(screen.getByLabelText('Add a note'), { target: { value: 'Agreement signed' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(spy.updateLead).toHaveBeenCalledWith('c1', { note: 'Agreement signed' }))
    expect(screen.getByTestId('outcome-summary')).toHaveTextContent('Won: ₹85 L')
  })
})

describe('lead list badge', () => {
  it('OutcomeBadge shows Won or Lost, nothing when open', () => {
    const base = { deal_price_inr: null, listing_id: null, lost_reason: null, closed_at: '' }
    const { rerender } = render(<OutcomeBadge outcome={{ ...base, result: 'won' }} />)
    expect(screen.getByText('Won')).toBeInTheDocument()
    rerender(<OutcomeBadge outcome={{ ...base, result: 'lost' }} />)
    expect(screen.getByText('Lost')).toBeInTheDocument()
    rerender(<OutcomeBadge outcome={null} />)
    expect(screen.queryByText('Won')).toBeNull()
    expect(screen.queryByText('Lost')).toBeNull()
  })

  it('the leads list shows the badge on won and lost cards only', async () => {
    await fx.updateLead('c1', { stage: 'won', outcome: {} })
    await fx.updateLead('c3', 'lost')
    render(<LeadsPage />)
    const card = async (name: string) => (await screen.findByText(name)).closest('a')!
    expect(within(await card('Rohit Deshmukh')).getByText('Won')).toBeInTheDocument()
    expect(within(await card('Imran Shaikh')).getByText('Lost')).toBeInTheDocument()
    const open = await card('Priya Nair')
    expect(within(open).queryByText('Won')).toBeNull()
    expect(within(open).queryByText('Lost')).toBeNull()
  })
})

const results = (over: Partial<TodayResults> = {}): TodayResults => ({
  period_days: 30, deals_won: 0, deal_value_inr: 0, deals_lost: 0, top_source: null, lost_reasons: {}, ...over,
})

describe('This month card on Home', () => {
  it('is hidden when there is nothing yet', () => {
    const { container, rerender } = render(<ResultsCard results={results()} />)
    expect(container).toBeEmptyDOMElement()
    rerender(<ResultsCard />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows deals won, total value in lakh/crore and the best channel', () => {
    render(<ResultsCard results={results({ deals_won: 2, deal_value_inr: 17_000_000, top_source: 'instagram' })} />)
    const card = within(screen.getByRole('region', { name: 'This month' }))
    expect(card.getByTestId('deals-won')).toHaveTextContent('2')
    expect(card.getByTestId('deal-value')).toHaveTextContent('₹1.7 Cr')
    expect(card.getByText('Best channel: Instagram')).toBeInTheDocument()
    expect(card.queryByTestId('lost-hint')).toBeNull()
  })

  it('omits the channel when none is set, and hints at the top lost reason', () => {
    render(<ResultsCard results={results({ deals_won: 1, deal_value_inr: 8_500_000, deals_lost: 3, lost_reasons: { price: 2, bought_elsewhere: 1 } })} />)
    expect(screen.queryByText(/Best channel/)).toBeNull()
    expect(screen.getByTestId('deal-value')).toHaveTextContent('₹85 L')
    expect(screen.getByTestId('lost-hint')).toHaveTextContent('Most lost on price')
  })

  it('shows a dash for value when deals were closed without a price, and lost-only months still show', () => {
    const { rerender } = render(<ResultsCard results={results({ deals_won: 1 })} />)
    expect(screen.getByTestId('deal-value')).toHaveTextContent('-')
    rerender(<ResultsCard results={results({ deals_lost: 1, lost_reasons: { changed_mind: 1 } })} />)
    expect(screen.getByTestId('lost-hint')).toHaveTextContent('Most lost on changed mind')
  })

  it('appears on Home from getToday().results, and stays off for the seeded fixture agent', async () => {
    getToday.mockResolvedValue(await fx.getToday())
    const { unmount } = render(<BusinessToday />)
    await screen.findByTestId('headline')
    expect(screen.queryByRole('region', { name: 'This month' })).toBeNull()
    unmount()

    await fx.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_500_000, listing_id: 'l1' } })
    getToday.mockResolvedValue(await fx.getToday())
    render(<BusinessToday />)
    const card = within(await screen.findByRole('region', { name: 'This month' }))
    expect(card.getByTestId('deals-won')).toHaveTextContent('1')
    expect(card.getByTestId('deal-value')).toHaveTextContent('₹85 L')
    expect(card.getByText('Best channel: Instagram')).toBeInTheDocument()
  })

  it('an older backend without results simply shows no card', async () => {
    const t: Today = { ...(await fx.getToday()) }
    delete t.results
    getToday.mockResolvedValue(t)
    render(<BusinessToday />)
    await screen.findByTestId('headline')
    expect(screen.queryByRole('region', { name: 'This month' })).toBeNull()
  })
})

describe('deals on listing cards', () => {
  it('shows deals and deal value next to the performance numbers when deals > 0', async () => {
    await fx.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_500_000, listing_id: 'l1' } })
    await fx.updateLead('c4', { stage: 'won', outcome: { deal_price_inr: 8_700_000, listing_id: 'l1' } })
    const listing = await fx.getListing('l1')
    const perf = (await fx.getPerformance()).find((p) => p.listing_id === 'l1')!
    const { rerender } = render(<ListingCard listing={listing} performance={perf} />)
    expect(screen.getByTestId('performance')).toBeInTheDocument()
    expect(screen.getByTestId('performance-deals')).toHaveTextContent('2 deals · ₹1.72 Cr')

    rerender(<ListingCard listing={listing} performance={{ ...perf, deals: 1, deal_value_inr: 0 }} />)
    expect(screen.getByTestId('performance-deals')).toHaveTextContent(/^1 deal$/)
  })

  it('shows nothing extra when there are no deals, or on an older backend', async () => {
    const listing = await fx.getListing('l1')
    const perf = (await fx.getPerformance()).find((p) => p.listing_id === 'l1')!
    const { rerender } = render(<ListingCard listing={listing} performance={perf} />)
    expect(screen.queryByTestId('performance-deals')).toBeNull()
    const old = { ...perf }
    delete old.deals
    delete old.deal_value_inr
    rerender(<ListingCard listing={listing} performance={old} />)
    expect(screen.queryByTestId('performance-deals')).toBeNull()
  })
})
