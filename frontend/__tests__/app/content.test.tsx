import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import ContentPage from '@/app/studio/content/page'
import { FIXTURE_ITEMS, countdown, createContentApi, groupItems, createFixtureContentApi, dueLabel, mediaUrl, normalizeItem, statusLabel } from '@/lib/app/content'
import type { ContentItem } from '@/lib/app/content'
import { ApiError } from '@/lib/app/api'

const getUpcoming = jest.fn()
const approve = jest.fn()
const skip = jest.fn()
const postNow = jest.fn()
const getRecent = jest.fn()
const unapprove = jest.fn()
const retry = jest.fn()
jest.mock('@/lib/app/client', () => ({
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok' }))
jest.mock('@/lib/app/content', () => ({
  ...jest.requireActual('@/lib/app/content'),
  contentApi: {
    getUpcoming: (...a: unknown[]) => getUpcoming(...a),
    approve: (...a: unknown[]) => approve(...a),
    skip: (...a: unknown[]) => skip(...a),
    postNow: (...a: unknown[]) => postNow(...a),
    getRecent: (...a: unknown[]) => getRecent(...a),
    unapprove: (...a: unknown[]) => unapprove(...a),
    retry: (...a: unknown[]) => retry(...a),
  },
}))

const okRes = (body: unknown, status = 200) => ({ ok: status < 400, status, text: async () => JSON.stringify(body) })
const items = (): ContentItem[] => FIXTURE_ITEMS.map((i) => ({ ...i }))

beforeEach(() => {
  ;[getUpcoming, approve, skip, postNow, getRecent, unapprove, retry].forEach((m) => m.mockReset())
  window.history.replaceState(null, '', '/studio/content')
  postNow.mockResolvedValue(undefined)
  getRecent.mockResolvedValue([])
  getUpcoming.mockResolvedValue(items())
  approve.mockResolvedValue(undefined)
  skip.mockResolvedValue(undefined)
})


const openRow = async (n = 0) => {
  const cards = await screen.findAllByTestId('content-card')
  fireEvent.click(within(cards[n]).getAllByRole('button')[0])
  return within(screen.getAllByTestId('content-card')[n])
}

describe('Content screen: tabs, compact rows, guarded actions', () => {
  it('opens on To approve with counts on every tab, rows show a title, channels and a status', async () => {
    render(<ContentPage />)
    const tabs = await screen.findByRole('tablist', { name: 'Content' })
    expect(within(tabs).getByRole('tab', { name: /To approve\s*2/ })).toHaveAttribute('aria-selected', 'true')
    expect(within(tabs).getByRole('tab', { name: /Going out\s*1/ })).toBeInTheDocument()
    expect(within(tabs).queryByRole('tab', { name: /Problems/ })).toBeNull()
    const cards = screen.getAllByTestId('content-card')
    expect(cards).toHaveLength(2)
    expect(within(cards[0]).getByTestId('row-title')).toHaveTextContent('Ask these water and power questions')
    expect(within(cards[0]).getByLabelText('Instagram')).toBeInTheDocument()
    expect(within(cards[0]).getByText('Needs your OK')).toBeInTheDocument()
    expect(within(cards[0]).queryByTestId('caption')).toBeNull()
  })

  it('a tapped row shows images, caption and actions; Approve moves it to Going out', async () => {
    render(<ContentPage />)
    const card = await openRow(0)
    expect(card.getAllByRole('img').length).toBeGreaterThan(0)
    expect(card.getByTestId('caption')).toHaveTextContent('Ask these water and power questions')
    fireEvent.click(card.getByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(approve).toHaveBeenCalledWith('fx-1'))
    await waitFor(() => expect(screen.getByRole('tab', { name: /To approve\s*1/ })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('tab', { name: /Going out/ }))
    expect(window.location.search).toBe('?tab=going')
    expect(screen.getAllByTestId('content-card')).toHaveLength(2)
  })

  it('Post now asks first, then posts every open copy', async () => {
    render(<ContentPage />)
    const card = await openRow(0)
    fireEvent.click(card.getByRole('button', { name: 'Post now…' }))
    expect(postNow).not.toHaveBeenCalled()
    const sheet = screen.getByRole('dialog', { name: /Post now on Instagram/ })
    fireEvent.click(within(sheet).getByRole('button', { name: 'Yes, post now' }))
    await waitFor(() => expect(postNow).toHaveBeenCalledWith('fx-1'))
  })

  it('Skip can be undone for a few seconds, then goes to the server', async () => {
    render(<ContentPage />)
    const card = await openRow(0)
    jest.useFakeTimers()
    try {
      fireEvent.click(card.getByRole('button', { name: 'Skip' }))
      expect(screen.getByRole('status')).toHaveTextContent('Skipped')
      fireEvent.click(screen.getByRole('button', { name: 'Undo' }))
      expect(skip).not.toHaveBeenCalled()
      expect(screen.getAllByTestId('content-card')).toHaveLength(2)
      fireEvent.click(within(screen.getAllByTestId('content-card')[0]).getAllByRole('button')[0])
      fireEvent.click(within(screen.getAllByTestId('content-card')[0]).getByRole('button', { name: 'Skip' }))
      jest.advanceTimersByTime(8100)
    } finally {
      jest.useRealTimers()
    }
    await waitFor(() => expect(skip).toHaveBeenCalledWith('fx-1'))
  })

  it('Approve all asks first', async () => {
    render(<ContentPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Approve all 2' }))
    fireEvent.click(within(screen.getByRole('dialog', { name: /Approve all 2 posts/ })).getByRole('button', { name: 'Approve 2' }))
    await waitFor(() => expect(approve).toHaveBeenCalledTimes(2))
  })

  it('an approved post can go back to To approve', async () => {
    unapprove.mockResolvedValue(undefined)
    window.history.replaceState(null, '', '/studio/content?tab=going')
    render(<ContentPage />)
    const card = await openRow(0)
    fireEvent.click(card.getByRole('button', { name: 'Back to To approve' }))
    await waitFor(() => expect(unapprove).toHaveBeenCalledWith('fx-3'))
  })

  it('a refused action shows a friendly message', async () => {
    approve.mockRejectedValue(new ApiError(409, 'x'))
    render(<ContentPage />)
    const card = await openRow(0)
    fireEvent.click(card.getByRole('button', { name: 'Approve' }))
    expect(await screen.findByText(/already handled/)).toBeInTheDocument()
  })

  it('loading errors offer a retry; an empty queue says what to expect', async () => {
    getUpcoming.mockRejectedValueOnce(new Error('boom'))
    render(<ContentPage />)
    expect(await screen.findByText(/boom/)).toBeInTheDocument()
    getUpcoming.mockResolvedValue([])
    fireEvent.click(screen.getByRole('button', { name: /try again|retry/i }))
    expect(await screen.findByText(/Nothing approved is waiting to go out/)).toBeInTheDocument()
  })
})

describe('Instagram and Facebook copies, duplicates, posted and problems', () => {
  const pair = (): ContentItem[] => [
    { ...FIXTURE_ITEMS[0], id: 'ig-1', channel: 'instagram', status: 'approved', due_at: new Date(Date.now() + 3 * 3600_000).toISOString() },
    { ...FIXTURE_ITEMS[0], id: 'fb-1', channel: 'facebook_page', status: 'planned', due_at: new Date(Date.now() + 4 * 3600_000).toISOString() },
  ]

  it('one row for both copies; opened, each channel says when it goes out', async () => {
    getUpcoming.mockResolvedValue(pair())
    render(<ContentPage />)
    expect(await screen.findAllByTestId('content-card')).toHaveLength(1)
    const card = await openRow(0)
    expect(card.getByTestId('when')).toHaveTextContent(/Goes out in (2h 5\dm|3h 0m)/)
    expect(card.getByTestId('when')).toHaveTextContent(/Needs your OK/)
    fireEvent.click(card.getByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(approve).toHaveBeenCalledWith('fb-1'))
    expect(approve).toHaveBeenCalledTimes(1)
  })

  it('a repeat of a published post is flagged and cannot be posted now', async () => {
    getUpcoming.mockResolvedValue([{ ...pair()[1], duplicate_of: { slug: 'hd-goyal-my-home', published_at: '2026-10-03T12:11:00Z', permalink: null } }])
    render(<ContentPage />)
    const card = await openRow(0)
    expect(card.getByTestId('duplicate')).toHaveTextContent(/repeats .hd-goyal-my-home.*held back/)
    expect(card.queryByRole('button', { name: 'Post now…' })).toBeNull()
  })

  it('Posted lists links per channel; Problems shows the reason and Retry', async () => {
    retry.mockResolvedValue(undefined)
    getUpcoming.mockResolvedValue([])
    getRecent.mockResolvedValue([
      { ...FIXTURE_ITEMS[0], id: 'p-ig', channel: 'instagram', status: 'published', permalink: 'https://www.instagram.com/p/X/', published_at: '2026-10-06T17:48:00Z' },
      { ...FIXTURE_ITEMS[1], id: 'p-fb', channel: 'facebook_page', status: 'failed', error: 'Application request limit reached' },
    ])
    render(<ContentPage />)
    fireEvent.click(await screen.findByRole('tab', { name: /Posted\s*1/ }))
    expect(within(screen.getByTestId('posted')).getByRole('link', { name: /Open post/ })).toHaveAttribute('href', 'https://www.instagram.com/p/X/')
    fireEvent.click(screen.getByRole('tab', { name: /Problems\s*1/ }))
    const card = await openRow(0)
    expect(card.getByText('Application request limit reached')).toBeInTheDocument()
    fireEvent.click(card.getByRole('button', { name: 'Retry' }))
    await waitFor(() => expect(retry).toHaveBeenCalledWith('p-fb'))
  })

  it('countdown and grouping helpers', () => {
    const now = Date.parse('2026-10-06T10:00:00Z')
    expect(countdown('2026-10-06T10:20:00Z', now)).toBe('in 20 min')
    expect(countdown('2026-10-06T12:30:00Z', now)).toBe('in 2h 30m')
    expect(countdown('2026-10-09T10:00:00Z', now)).toBe('in 3 days')
    expect(countdown('2026-10-06T09:00:00Z', now)).toBeNull()
    const g = groupItems([{ ...FIXTURE_ITEMS[0], id: 'a', channel: 'facebook_page' }, { ...FIXTURE_ITEMS[1], id: 'b' }, { ...FIXTURE_ITEMS[0], id: 'c', channel: 'instagram' }])
    expect(g.map((x) => x.items.map((i) => i.id))).toEqual([['c', 'a'], ['b']])
  })
})

describe('content client', () => {
  it('normalizes loose rows', () => {
    const n = normalizeItem({ id: 7, kind: 'weird', channel: 'facebook_page', image_urls: null, status: 'approved', week: '2' })
    expect(n).toMatchObject({ id: '7', kind: 'post', channel: 'facebook_page', image_urls: [], status: 'approved', week: null, video_url: null })
  })

  it('formats due times in India time and builds media urls', () => {
    expect(dueLabel('2026-10-12T04:30:00Z')).toBe('Mon 12 Oct, 10:00 am')
    expect(dueLabel('2026-10-12T13:30:00')).toBe('Mon 12 Oct, 7:00 pm')
    expect(dueLabel('nope')).toBe('')
    expect(mediaUrl('/uploads/a.jpg', 'https://api.test')).toBe('https://api.test/uploads/a.jpg')
    expect(mediaUrl('data:image/svg+xml;utf8,x', 'https://api.test')).toBe('data:image/svg+xml;utf8,x')
    expect(statusLabel('scheduled')).toBe('Approved')
  })

  it('talks to /calendar with the bearer token', async () => {
    const calls: Array<[string, RequestInit]> = []
    const fetchImpl = jest.fn(async (url: string, init: RequestInit) => {
      calls.push([url, init])
      return okRes(url.includes('/upcoming') ? [{ id: 'a', slug: 's', channel: 'instagram', due_at: 'x', caption: 'c' }] : {})
    }) as unknown as typeof fetch
    const api = createContentApi({ getToken: () => 'tok', baseUrl: 'https://api.test', fetchImpl })
    expect((await api.getUpcoming(5))[0].id).toBe('a')
    await api.approve('a b')
    await api.skip('a')
    expect(calls.map(([u, i]) => `${i.method} ${u}`)).toEqual([
      'GET https://api.test/api/v1/calendar/upcoming?limit=5',
      'POST https://api.test/api/v1/calendar/items/a%20b/approve',
      'POST https://api.test/api/v1/calendar/items/a/skip',
    ])
    expect((calls[0][1].headers as Record<string, string>).Authorization).toBe('Bearer tok')
  })

  it('rejects a 403 with an ApiError', async () => {
    const fetchImpl = jest.fn(async () => okRes({ detail: 'no' }, 403)) as unknown as typeof fetch
    await expect(createContentApi({ getToken: () => null, baseUrl: 'https://api.test', fetchImpl }).getUpcoming()).rejects.toMatchObject({ status: 403 })
  })

  it('the fixture api approves once, then refuses, and skip removes', async () => {
    const api = createFixtureContentApi()
    await api.approve('fx-1')
    await expect(api.approve('fx-1')).rejects.toMatchObject({ status: 409 })
    await api.skip('fx-2')
    expect((await api.getUpcoming()).map((i) => i.id)).toEqual(['fx-1', 'fx-3'])
    await expect(api.skip('nope')).rejects.toMatchObject({ status: 404 })
  })
})


