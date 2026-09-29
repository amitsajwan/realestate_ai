import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { ApiError } from '@/lib/app/api'
import { BusinessToday } from '@/components/app/BusinessToday'
import { ListingCard } from '@/components/app/ListingCard'
import { MarketingPackView } from '@/components/app/MarketingPackView'
import { MarketingScreen } from '@/components/app/MarketingScreen'
import { MatchingBuyersCard, MatchingBuyersList } from '@/components/app/MatchingBuyersCard'
import { createFixtureApi } from '@/lib/app/fixtures'
import type { MarketingPack } from '@/lib/app/types'

const createMarketingPack = jest.fn()
const getMarketingPack = jest.fn()
const getMatchingLeads = jest.fn()
const getToday = jest.fn()
const listLeads = jest.fn()
jest.mock('@/lib/app/client', () => ({
  api: {
    createMarketingPack: (...a: unknown[]) => createMarketingPack(...a),
    getMarketingPack: (...a: unknown[]) => getMarketingPack(...a),
    getMatchingLeads: (...a: unknown[]) => getMatchingLeads(...a),
    getToday: (...a: unknown[]) => getToday(...a),
    listLeads: (...a: unknown[]) => listLeads(...a),
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
jest.mock('@/lib/app/session', () => ({ useSession: () => ({ siteUrl: null, logout: jest.fn() }) }))

const mem = () => ({ getItem: () => null, setItem: () => undefined })
const fx = () => createFixtureApi(mem())

let clipboard: jest.Mock
const nav = navigator as unknown as Record<string, unknown>

beforeEach(() => {
  ;[createMarketingPack, getMarketingPack, getMatchingLeads, getToday, listLeads].forEach((m) => m.mockReset())
  clipboard = jest.fn().mockResolvedValue(undefined)
  Object.defineProperty(navigator, 'clipboard', { value: { writeText: clipboard }, configurable: true })
  delete nav.share
  delete nav.canShare
  window.open = jest.fn()
  // @ts-expect-error tests decide whether fetch works
  global.fetch = undefined
})

describe('MarketingScreen', () => {
  it('shows the skeleton while creating, then every channel card and an honest publish section', async () => {
    const pack = await fx().createMarketingPack('l1')
    let resolve!: (p: MarketingPack) => void
    createMarketingPack.mockReturnValue(new Promise<MarketingPack>((r) => (resolve = r)))
    getMatchingLeads.mockResolvedValue({ listing: {}, buyers: [] })
    render(<MarketingScreen listingId="l1" autoCreate />)

    expect(screen.getByText('Creating your marketing...', { selector: 'p' })).toBeInTheDocument()
    expect(screen.getByTestId('pack-skeleton')).toBeInTheDocument()
    expect(createMarketingPack).toHaveBeenCalledWith('l1', undefined)

    await act(async () => resolve(pack))
    expect(screen.queryByTestId('pack-skeleton')).toBeNull()
    for (const name of ['Instagram', 'Facebook', 'WhatsApp', 'Reel script']) {
      expect(screen.getByRole('region', { name })).toBeInTheDocument()
    }
    expect(screen.getByTestId('carousel').querySelectorAll('img')).toHaveLength(4)
    expect(screen.getByTestId('ig-caption')).toHaveTextContent(pack.instagram.caption)
    expect(screen.getByTestId('fb-post')).toHaveTextContent('New property')
    expect(screen.getByTestId('wa-status')).toHaveTextContent(pack.whatsapp.status_text)
    expect(screen.getByTestId('reel-beats').querySelectorAll('li')).toHaveLength(pack.reel.beats.length)

    const publish = screen.getByRole('region', { name: 'Publish everywhere' })
    expect(publish).toHaveTextContent(/for now you copy or share each item yourself/i)
    for (const name of [/Connect Instagram/, /Connect Facebook/, /Connect WhatsApp Business/]) {
      const b = within(publish).getByRole('button', { name })
      expect(b).toBeDisabled()
      expect(b).toHaveTextContent('Coming soon')
    }
  })

  it('opens a saved pack with GET and creates one when there is none (404)', async () => {
    const pack = await fx().createMarketingPack('l1')
    getMatchingLeads.mockResolvedValue({ listing: {}, buyers: [] })
    getMarketingPack.mockResolvedValue(pack)
    const { unmount } = render(<MarketingScreen listingId="l1" />)
    expect(await screen.findByTestId('pack')).toBeInTheDocument()
    expect(createMarketingPack).not.toHaveBeenCalled()
    unmount()

    getMarketingPack.mockRejectedValue(new ApiError(404, 'none'))
    createMarketingPack.mockResolvedValue(pack)
    render(<MarketingScreen listingId="l1" />)
    expect(await screen.findByTestId('pack')).toBeInTheDocument()
    expect(createMarketingPack).toHaveBeenCalledTimes(1)
  })

  it('shows a friendly retry when generation fails and recovers on retry', async () => {
    const pack = await fx().createMarketingPack('l1')
    getMatchingLeads.mockResolvedValue({ listing: {}, buyers: [] })
    createMarketingPack.mockRejectedValueOnce(new ApiError(500, 'boom')).mockResolvedValueOnce(pack)
    render(<MarketingScreen listingId="l1" autoCreate />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Your property is already live')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByTestId('pack')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('switches language, and reports when the language used differs from the one asked for', async () => {
    const f = fx()
    getMatchingLeads.mockResolvedValue({ listing: {}, buyers: [] })
    createMarketingPack.mockImplementation((id: string, lang?: 'en' | 'hi' | 'mr') => f.createMarketingPack(id, lang))
    render(<MarketingScreen listingId="l1" autoCreate />)
    await screen.findByTestId('pack')

    fireEvent.click(screen.getByRole('button', { name: 'HI' }))
    await waitFor(() => expect(createMarketingPack).toHaveBeenLastCalledWith('l1', 'hi'))
    await waitFor(() => expect(screen.getByRole('button', { name: 'HI' })).toHaveAttribute('aria-pressed', 'true'))
    expect(await screen.findByTestId('ig-caption')).toHaveTextContent('साइट विज़िट')
    expect(screen.queryByText(/not ready yet/)).toBeNull()

    fireEvent.click(screen.getByRole('button', { name: 'MR' }))
    expect(await screen.findByText(/This language is not ready yet, so your marketing is in English/)).toBeInTheDocument()
    expect(createMarketingPack).toHaveBeenLastCalledWith('l1', 'mr')
  })
})

describe('MarketingPackView', () => {
  async function pack() {
    return fx().createMarketingPack('l1')
  }

  it('copies caption + hashtags, and each channel text, with a "Copied!" confirmation', async () => {
    const p = await pack()
    render(<MarketingPackView pack={p} />)
    fireEvent.click(screen.getByRole('button', { name: 'Copy caption' }))
    await waitFor(() => expect(clipboard).toHaveBeenCalledTimes(1))
    expect(clipboard.mock.calls[0][0]).toBe(`${p.instagram.caption}\n\n${p.instagram.hashtags.map((h) => `#${h}`).join(' ')}`)
    expect(await screen.findByRole('button', { name: 'Copied!' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Copy post' }))
    await waitFor(() => expect(clipboard).toHaveBeenLastCalledWith(p.facebook.post))
    fireEvent.click(screen.getByRole('button', { name: 'Copy message' }))
    await waitFor(() => expect(clipboard).toHaveBeenLastCalledWith(p.whatsapp.message))
    fireEvent.click(screen.getByRole('button', { name: 'Copy script' }))
    await waitFor(() => expect(clipboard.mock.calls[clipboard.mock.calls.length - 1][0]).toMatch(/^Hook: .*\n1\. \(0-3\)/))
  })

  it('sends the WhatsApp message through a wa.me link (nothing is sent automatically)', async () => {
    const p = await pack()
    render(<MarketingPackView pack={p} />)
    const wa = within(screen.getByRole('region', { name: 'WhatsApp' }))
    expect(wa.getByRole('link', { name: 'Send on WhatsApp' })).toHaveAttribute('href', `https://wa.me/?text=${encodeURIComponent(p.whatsapp.message)}`)
    expect(wa.getByRole('button', { name: 'Download status image' })).toBeInTheDocument()
  })

  it('share falls back to download/open when the phone cannot share files', async () => {
    const p = await pack()
    render(<MarketingPackView pack={p} />)
    fireEvent.click(screen.getByRole('button', { name: 'Share' }))
    await waitFor(() => expect(window.open).toHaveBeenCalledWith(p.instagram.images[0].url, '_blank', 'noopener,noreferrer'))
    expect(await screen.findByRole('status')).toHaveTextContent(/Image opened/)
  })

  it('share uses navigator.share with the image file when supported', async () => {
    const p = await pack()
    const share = jest.fn().mockResolvedValue(undefined)
    nav.share = share
    nav.canShare = jest.fn().mockReturnValue(true)
    global.fetch = jest.fn().mockResolvedValue({ blob: async () => new Blob(['x'], { type: 'image/svg+xml' }) }) as unknown as typeof fetch
    render(<MarketingPackView pack={p} />)
    fireEvent.click(screen.getByRole('button', { name: 'Share' }))
    await waitFor(() => expect(share).toHaveBeenCalledTimes(1))
    const arg = share.mock.calls[0][0]
    expect(arg.files).toHaveLength(1)
    expect(arg.files[0].name).toBe('l1-cover.svg')
    expect(arg.text).toContain(p.instagram.caption)
    expect(window.open).not.toHaveBeenCalled()
  })

  it('download saves via an anchor when fetch works', async () => {
    const p = await pack()
    global.fetch = jest.fn().mockResolvedValue({ blob: async () => new Blob(['x']) }) as unknown as typeof fetch
    URL.createObjectURL = jest.fn().mockReturnValue('blob:x')
    URL.revokeObjectURL = jest.fn()
    const click = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)
    render(<MarketingPackView pack={p} />)
    fireEvent.click(screen.getByRole('button', { name: 'Download image' }))
    await waitFor(() => expect(click).toHaveBeenCalled())
    expect(window.open).not.toHaveBeenCalled()
    click.mockRestore()
  })
})

describe('matching buyers card', () => {
  it('shows "N of your buyers match", rows with % and reasons, and the never-sends note', async () => {
    const r = await fx().getMatchingLeads('l1')
    getMatchingLeads.mockResolvedValue(r)
    render(<MatchingBuyersCard listingId="l1" />)
    expect(await screen.findByRole('heading', { name: `${r.buyers.length} of your buyers match this property` })).toBeInTheDocument()
    expect(getMatchingLeads).toHaveBeenCalledWith('l1')
    const b = r.buyers[0]
    const row = within(screen.getByTestId(`buyer-${b.lead_id}`))
    expect(row.getByText(b.name)).toBeInTheDocument()
    expect(row.getByText(b.requirement_line!)).toBeInTheDocument()
    expect(row.getByText(`${b.match_pct}% match`)).toBeInTheDocument()
    b.reasons.forEach((reason) => expect(row.getByText(reason)).toBeInTheDocument())
    expect(row.getByRole('link', { name: /Send on WhatsApp/ })).toHaveAttribute('href', b.draft.whatsapp_url)
    expect(screen.getByText('We never send anything for you.')).toBeInTheDocument()
  })

  it('lets the agent edit the draft; the wa.me link follows the edited, encoded text', async () => {
    const r = await fx().getMatchingLeads('l1')
    render(<MatchingBuyersList buyers={r.buyers} />)
    const b = r.buyers[0]
    const row = within(screen.getByTestId(`buyer-${b.lead_id}`))
    expect(row.queryByRole('textbox')).toBeNull()
    fireEvent.click(row.getByRole('button', { name: 'Edit message' }))
    const box = row.getByRole('textbox') as HTMLTextAreaElement
    expect(box.value).toBe(b.draft.message)
    fireEvent.change(box, { target: { value: 'Hello & welcome, ₹85 L?' } })
    const digits = b.phone.replace(/\D/g, '')
    expect(row.getByRole('link', { name: /Send on WhatsApp/ })).toHaveAttribute('href', `https://wa.me/${digits}?text=${encodeURIComponent('Hello & welcome, ₹85 L?')}`)
    fireEvent.click(row.getByRole('button', { name: 'Hide message' }))
    expect(row.queryByRole('textbox')).toBeNull()
  })

  it('shows a friendly line when no buyer matches, and an error with retry when loading fails', async () => {
    getMatchingLeads.mockResolvedValue({ listing: {}, buyers: [] })
    const { unmount } = render(<MatchingBuyersCard listingId="l2" />)
    expect(await screen.findByText(/None of your buyers match this property yet/)).toBeInTheDocument()
    expect(screen.getByRole('heading')).toHaveTextContent('0 of your buyers match this property')
    expect(screen.getByText('We never send anything for you.')).toBeInTheDocument()
    unmount()

    getMatchingLeads.mockRejectedValue(new Error('down'))
    render(<MatchingBuyersCard listingId="l2" />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load matching buyers')
  })
})

describe('recommended actions on home', () => {
  it('lists each type with the right primary button target, above the headline and tiles', async () => {
    const f = fx()
    getToday.mockResolvedValue(await f.getToday())
    listLeads.mockResolvedValue(await f.listLeads())
    render(<BusinessToday />)
    const region = await screen.findByRole('region', { name: 'AI recommends' })
    const btn = (type: string) => within(within(region).getByTestId(`action-${type}`)).getAllByRole('link').slice(-1)[0]
    expect(btn('call')).toHaveAttribute('href', '/studio/leads/c1')
    expect(btn('call')).toHaveTextContent('Call now')
    expect(btn('follow_up')).toHaveAttribute('href', '/studio/leads/c2')
    expect(btn('follow_up')).toHaveTextContent('Follow up')
    expect(btn('send_property')).toHaveAttribute('href', '/studio/listings/l1/marketing')
    expect(btn('send_property')).toHaveTextContent('Send property')
    const create = within(region).getAllByTestId('action-create_marketing')[0]
    expect(within(create).getAllByRole('link').slice(-1)[0]).toHaveAttribute('href', expect.stringMatching(/^\/studio\/listings\/l\d+\/marketing$/))
    expect(within(create).getAllByRole('link').slice(-1)[0]).toHaveTextContent('Create marketing')
    // the whole card text is tappable too
    expect(within(within(region).getByTestId('action-call')).getAllByRole('link')[0]).toHaveAttribute('href', '/studio/leads/c1')

    expect(region.compareDocumentPosition(screen.getByTestId('headline')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByRole('region', { name: 'Hot buyers' })).toBeInTheDocument()
  })

  it('renders nothing extra when there are no actions', async () => {
    getToday.mockResolvedValue({
      counts: { new_enquiries_24h: 1, hot: 0, site_visits: 0, follow_ups_due: 0, uncontacted: 1 },
      hot_buyers: [], follow_ups: [], headline: 'x',
    })
    listLeads.mockResolvedValue([])
    render(<BusinessToday />)
    await screen.findByTestId('headline')
    expect(screen.queryByRole('region', { name: 'AI recommends' })).toBeNull()
  })
})

describe('performance on listing cards', () => {
  it('shows views, enquiries, qualified and site visits when available, nothing when not', async () => {
    const f = fx()
    const listing = await f.getListing('l1')
    const perf = (await f.getPerformance()).find((p) => p.listing_id === 'l1')!
    const { rerender } = render(<ListingCard listing={listing} performance={perf} />)
    const stats = within(screen.getByTestId('performance'))
    expect(stats.getByText(String(perf.views)).nextSibling).toHaveTextContent('views')
    expect(stats.getByText('enquiries')).toBeInTheDocument()
    expect(stats.getByText('qualified')).toBeInTheDocument()
    expect(stats.getByText('site visits')).toBeInTheDocument()
    rerender(<ListingCard listing={listing} />)
    expect(screen.queryByTestId('performance')).toBeNull()
  })
})
