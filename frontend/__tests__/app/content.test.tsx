import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import ContentPage from '@/app/studio/content/page'
import { FIXTURE_ITEMS, createContentApi, createFixtureContentApi, dueLabel, mediaUrl, normalizeItem, statusLabel } from '@/lib/app/content'
import type { ContentItem } from '@/lib/app/content'
import { ApiError } from '@/lib/app/api'

const getUpcoming = jest.fn()
const approve = jest.fn()
const skip = jest.fn()
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
  },
}))

const okRes = (body: unknown, status = 200) => ({ ok: status < 400, status, text: async () => JSON.stringify(body) })
const items = (): ContentItem[] => FIXTURE_ITEMS.map((i) => ({ ...i }))

beforeEach(() => {
  ;[getUpcoming, approve, skip].forEach((m) => m.mockReset())
  getUpcoming.mockResolvedValue(items())
  approve.mockResolvedValue(undefined)
  skip.mockResolvedValue(undefined)
})

describe('Content screen', () => {
  it('lists cards with channel, kind, due time, caption and a scrolling image carousel', async () => {
    render(<ContentPage />)
    const cards = await screen.findAllByTestId('content-card')
    expect(cards).toHaveLength(3)
    const c = within(cards[0])
    expect(c.getByText('Instagram')).toBeInTheDocument()
    expect(c.getByText('Post')).toBeInTheDocument()
    expect(c.getByText('Needs your OK')).toBeInTheDocument()
    expect(c.getByTestId('caption')).toHaveTextContent('Ask these water and power questions')
    expect(c.getAllByRole('img')).toHaveLength(3)
    expect(c.getByTestId('carousel').className).toContain('overflow-x-auto')
    expect(within(cards[1]).getByText('Facebook')).toBeInTheDocument()
    expect(within(cards[1]).getByText('Sample home')).toBeInTheDocument()
    expect(within(cards[2]).getByTestId('reel-note')).toBeInTheDocument()
    expect(screen.getByText(/2 waiting for your OK/)).toBeInTheDocument()
  })

  it('approves a planned item and shows it as approved, without an Approve button', async () => {
    render(<ContentPage />)
    const cards = await screen.findAllByTestId('content-card')
    fireEvent.click(within(cards[0]).getByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(approve).toHaveBeenCalledWith('fx-1'))
    await waitFor(() => expect(within(screen.getAllByTestId('content-card')[0]).getByText('Approved')).toBeInTheDocument())
    expect(within(screen.getAllByTestId('content-card')[0]).queryByRole('button', { name: 'Approve' })).toBeNull()
    expect(screen.getByText(/1 waiting for your OK/)).toBeInTheDocument()
  })

  it('an already approved item only offers Skip; skipping removes the card', async () => {
    render(<ContentPage />)
    const cards = await screen.findAllByTestId('content-card')
    const reel = within(cards[2])
    expect(reel.queryByRole('button', { name: 'Approve' })).toBeNull()
    fireEvent.click(reel.getByRole('button', { name: 'Skip' }))
    await waitFor(() => expect(skip).toHaveBeenCalledWith('fx-3'))
    await waitFor(() => expect(screen.getAllByTestId('content-card')).toHaveLength(2))
  })

  it('shows a friendly message when the server refuses', async () => {
    approve.mockRejectedValue(new ApiError(409, 'x'))
    render(<ContentPage />)
    const cards = await screen.findAllByTestId('content-card')
    fireEvent.click(within(cards[0]).getByRole('button', { name: 'Approve' }))
    expect(await screen.findByText(/already handled/)).toBeInTheDocument()
    expect(within(screen.getAllByTestId('content-card')[0]).getByText('Needs your OK')).toBeInTheDocument()
  })

  it('shows an error box with retry when loading fails, and an empty state', async () => {
    getUpcoming.mockRejectedValueOnce(new Error('boom'))
    render(<ContentPage />)
    expect(await screen.findByText(/boom/)).toBeInTheDocument()
    getUpcoming.mockResolvedValue([])
    fireEvent.click(screen.getByRole('button', { name: /try again|retry/i }))
    expect(await screen.findByText(/No upcoming posts/)).toBeInTheDocument()
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
