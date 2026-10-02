import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import NewsroomPage from '@/app/studio/newsroom/page'
import {
  FIXTURE_QUEUE,
  FIXTURE_STATUS,
  ageLabel,
  createFixtureNewsroomApi,
  createNewsroomApi,
  normalizeItem,
  pillarLabel,
  whenToIso,
} from '@/lib/app/newsroom'
import type { NewsroomItem, NewsroomStatus } from '@/lib/app/newsroom'
import { ApiError } from '@/lib/app/api'

const getQueue = jest.fn()
const getStatus = jest.fn()
const approve = jest.fn()
const reject = jest.fn()
const mahareraRoundup = jest.fn()
jest.mock('@/lib/app/client', () => ({
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok' }))
jest.mock('@/lib/app/newsroom', () => ({
  ...jest.requireActual('@/lib/app/newsroom'),
  newsroomApi: {
    getQueue: (...a: unknown[]) => getQueue(...a),
    getStatus: (...a: unknown[]) => getStatus(...a),
    approve: (...a: unknown[]) => approve(...a),
    reject: (...a: unknown[]) => reject(...a),
    mahareraRoundup: (...a: unknown[]) => mahareraRoundup(...a),
  },
}))

const status = (over: Partial<NewsroomStatus> = {}): NewsroomStatus => ({ ...FIXTURE_STATUS, ...over })
const items = (): NewsroomItem[] => FIXTURE_QUEUE.map((i) => ({ ...i }))

beforeEach(() => {
  ;[getQueue, getStatus, approve, reject, mahareraRoundup].forEach((m) => m.mockReset())
  getQueue.mockResolvedValue(items())
  getStatus.mockResolvedValue(status())
  approve.mockResolvedValue({})
  reject.mockResolvedValue(undefined)
})

describe('Newsroom screen', () => {
  it('lists cards with pillar, areas, title, age, draft, sources', async () => {
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    expect(cards).toHaveLength(2)
    const c = within(cards[0])
    expect(c.getByText('Infrastructure')).toBeInTheDocument()
    expect(c.getByText('Hinjewadi')).toBeInTheDocument()
    expect(c.getByText('Baner')).toBeInTheDocument()
    expect(c.getByRole('heading', { level: 2 })).toHaveTextContent('Pune Metro Line 3')
    expect(c.getByText('1 day old')).toBeInTheDocument()
    expect((c.getByLabelText('Post text') as HTMLTextAreaElement).value).toContain('crossed 90 percent')
    expect(c.getByRole('link', { name: 'Times of India' })).toHaveAttribute('href', 'https://example.test/metro-line-3')
  })

  it('shows facts collapsed with their source quotes', async () => {
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    const details = cards[0].querySelector('details') as HTMLDetailsElement
    expect(details.open).toBe(false)
    expect(within(cards[0]).getByText('Facts and source quotes (2)')).toBeInTheDocument()
    expect(within(cards[0]).getByText(/Civil work on the Hinjewadi-Shivajinagar corridor/)).toBeInTheDocument()
  })

  it('shows a green check when ok and the list of problems otherwise', async () => {
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    expect(within(cards[0]).getByTestId('check-ok')).toBeInTheDocument()
    const bad = within(cards[1]).getByTestId('check-problems')
    expect(within(bad).getAllByRole('listitem')).toHaveLength(3)
    expect(bad).toHaveTextContent('Date "December 2031" is not in the source text.')
    expect(within(cards[1]).queryByTestId('check-ok')).toBeNull()
  })

  it('shows the status strip with counts, last run and last error', async () => {
    getStatus.mockResolvedValue(status({ last_error: 'Google News returned 503' }))
    render(<NewsroomPage />)
    await screen.findAllByTestId('queue-card')
    expect(screen.getByTestId('count-published')).toHaveTextContent('7')
    expect(screen.getByTestId('count-pending_review')).toHaveTextContent('2')
    expect(screen.getByText(/last run 1h ago/)).toBeInTheDocument()
    expect(screen.getByText(/Google News returned 503/)).toBeInTheDocument()
  })

  it('shows an empty state when the queue is empty', async () => {
    getQueue.mockResolvedValue([])
    render(<NewsroomPage />)
    expect(await screen.findByText(/Nothing to review right now/)).toBeInTheDocument()
    expect(screen.queryByTestId('queue-card')).toBeNull()
  })

  it('shows a clear banner when the newsroom is disabled', async () => {
    getQueue.mockResolvedValue([])
    getStatus.mockResolvedValue(status({ enabled: false }))
    render(<NewsroomPage />)
    expect(await screen.findByText(/newsroom is switched off/i)).toBeInTheDocument()
  })

  it('shows an error with retry when the queue cannot be loaded', async () => {
    getQueue.mockRejectedValueOnce(new Error('The newsroom is only for the owner.'))
    render(<NewsroomPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('only for the owner')
    fireEvent.click(screen.getByRole('button', { name: /try again/i }))
    expect(await screen.findAllByTestId('queue-card')).toHaveLength(2)
  })

  it('approves with no body when unedited, and removes the card', async () => {
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    fireEvent.click(within(cards[0]).getByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(screen.getAllByTestId('queue-card')).toHaveLength(1))
    expect(approve).toHaveBeenCalledWith('gn-metro-hinjewadi-1', {})
    expect(screen.getByTestId('count-pending_review')).toHaveTextContent('1')
  })

  it('sends edited text and flags it for re-check', async () => {
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    const box = within(cards[0]).getByLabelText('Post text')
    fireEvent.change(box, { target: { value: 'My own words. Thoughts?' } })
    expect(within(cards[0]).getByText(/Edited, will be re-checked/)).toBeInTheDocument()
    fireEvent.click(within(cards[0]).getByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(approve).toHaveBeenCalled())
    expect(approve).toHaveBeenCalledWith('gn-metro-hinjewadi-1', { text: 'My own words. Thoughts?' })
  })

  it('schedules with the picked time as an ISO string', async () => {
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    fireEvent.click(within(cards[0]).getByRole('button', { name: 'Pick a time' }))
    fireEvent.change(within(cards[0]).getByLabelText(/Post at/), { target: { value: '2026-10-05T09:30' } })
    fireEvent.click(within(cards[0]).getByRole('button', { name: 'Approve and schedule' }))
    await waitFor(() => expect(approve).toHaveBeenCalled())
    expect(approve.mock.calls[0][1]).toEqual({ when: new Date('2026-10-05T09:30').toISOString() })
  })

  it('rejects with an optional reason', async () => {
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    fireEvent.click(within(cards[1]).getByRole('button', { name: 'Reject' }))
    fireEvent.change(within(cards[1]).getByLabelText(/Reason/), { target: { value: 'old news' } })
    fireEvent.click(within(cards[1]).getByRole('button', { name: 'Confirm reject' }))
    await waitFor(() => expect(reject).toHaveBeenCalledWith('mr-kharadi-2', 'old news'))
    await waitFor(() => expect(screen.getAllByTestId('queue-card')).toHaveLength(1))
  })

  it('rejects without a reason as undefined', async () => {
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    fireEvent.click(within(cards[1]).getByRole('button', { name: 'Reject' }))
    fireEvent.click(within(cards[1]).getByRole('button', { name: 'Confirm reject' }))
    await waitFor(() => expect(reject).toHaveBeenCalledWith('mr-kharadi-2', undefined))
  })

  it('keeps the card and shows the problem when approve fails', async () => {
    approve.mockRejectedValue(new ApiError(422, 'Check failed: date not in source'))
    render(<NewsroomPage />)
    const cards = await screen.findAllByTestId('queue-card')
    fireEvent.click(within(cards[1]).getByRole('button', { name: 'Approve' }))
    expect(await within(screen.getAllByTestId('queue-card')[1]).findByText(/Check failed: date not in source/)).toBeInTheDocument()
    expect(screen.getAllByTestId('queue-card')).toHaveLength(2)
    expect(within(screen.getAllByTestId('queue-card')[1]).getByRole('button', { name: 'Approve' })).toBeEnabled()
  })
})

describe('MahaRERA post button', () => {
  const button = () => screen.findByRole('button', { name: 'Make the MahaRERA post (last 30 days)' })

  it('queues the post with one click and reloads the queue', async () => {
    mahareraRoundup.mockResolvedValue({ id: 'maharera-1', created: true, projects: 4 })
    render(<NewsroomPage />)
    fireEvent.click(await button())
    expect(await screen.findByRole('status')).toHaveTextContent('Added to the queue below (4 projects).')
    expect(mahareraRoundup).toHaveBeenCalledTimes(1)
    await waitFor(() => expect(getQueue).toHaveBeenCalledTimes(2))
  })

  it('says so when one is already waiting', async () => {
    mahareraRoundup.mockResolvedValue({ id: 'maharera-1', created: false, projects: 4 })
    render(<NewsroomPage />)
    fireEvent.click(await button())
    expect(await screen.findByRole('status')).toHaveTextContent('One is already waiting for review below.')
  })

  it("shows the server's words when there is nothing to post", async () => {
    mahareraRoundup.mockRejectedValue(new ApiError(404, 'No project in Kharadi or Wagholi was listed or updated on MahaRERA in the last 30 days'))
    render(<NewsroomPage />)
    fireEvent.click(await button())
    expect(await screen.findByRole('status')).toHaveTextContent('No project in Kharadi or Wagholi')
  })
})

describe('newsroom client and helpers', () => {
  const okRes = (body: unknown, status = 200) => ({ ok: status < 400, status, text: async () => (body === undefined ? '' : JSON.stringify(body)) }) as unknown as Response

  it('calls the contract endpoints with the bearer token', async () => {
    const f = jest.fn().mockResolvedValue(okRes([]))
    const api = createNewsroomApi({ getToken: () => 'abc', baseUrl: 'http://x', fetchImpl: f as unknown as typeof fetch })
    await api.getQueue()
    await api.getStatus()
    await api.approve('i 1', { text: 'hi', when: '2026-10-05T04:00:00.000Z' })
    await api.reject('i1', 'old')
    await api.reject('i2')
    await api.mahareraRoundup!()
    const calls = f.mock.calls.map((c) => [c[0], c[1].method, c[1].body, c[1].headers.Authorization])
    expect(calls).toEqual([
      ['http://x/api/v1/newsroom/queue', 'GET', undefined, 'Bearer abc'],
      ['http://x/api/v1/newsroom/status', 'GET', undefined, 'Bearer abc'],
      ['http://x/api/v1/newsroom/items/i%201/approve', 'POST', JSON.stringify({ text: 'hi', when: '2026-10-05T04:00:00.000Z' }), 'Bearer abc'],
      ['http://x/api/v1/newsroom/items/i1/reject', 'POST', JSON.stringify({ reason: 'old' }), 'Bearer abc'],
      ['http://x/api/v1/newsroom/items/i2/reject', 'POST', '{}', 'Bearer abc'],
      ['http://x/api/v1/newsroom/maharera-roundup', 'POST', undefined, 'Bearer abc'],
    ])
  })

  it('throws ApiError for failures and for network errors', async () => {
    const api = createNewsroomApi({ getToken: () => null, fetchImpl: jest.fn().mockResolvedValue(okRes({ detail: 'Owner only' }, 403)) as unknown as typeof fetch })
    await expect(api.getQueue()).rejects.toMatchObject({ status: 403, detail: 'Owner only' })
    const down = createNewsroomApi({ getToken: () => null, fetchImpl: jest.fn().mockRejectedValue(new Error('x')) as unknown as typeof fetch })
    await expect(down.getStatus()).rejects.toMatchObject({ status: 0 })
  })

  it('normalizes loose item shapes', () => {
    const n = normalizeItem({ id: 'a', title: 'T', pillar: 'new_supply', draft: { text: 'body' }, check: { ok: true, problems: ['x'] }, sources: ['https://e.test/a', 'Plain'] })
    expect(n.draft).toBe('body')
    expect(n.check.ok).toBe(false)
    expect(n.sources).toEqual([{ name: 'https://e.test/a', url: 'https://e.test/a' }, { name: 'Plain', url: null }])
    expect(normalizeItem(null).areas).toEqual([])
  })

  it('formats labels and dates', () => {
    expect(pillarLabel('rules_money')).toBe('Rules and money')
    expect(pillarLabel('some_new_one')).toBe('Some new one')
    expect(ageLabel(0)).toBe('today')
    expect(ageLabel(4)).toBe('4 days old')
    expect(whenToIso('')).toBeUndefined()
    expect(whenToIso('nope')).toBeUndefined()
  })

  it('fixture api removes handled items and counts them', async () => {
    const f = createFixtureNewsroomApi()
    expect(await f.getQueue()).toHaveLength(2)
    await f.approve('mr-kharadi-2')
    await f.reject('gn-metro-hinjewadi-1')
    expect(await f.getQueue()).toEqual([])
    expect((await f.getStatus()).counts.pending_review).toBe(0)
    await expect(f.reject('gone')).rejects.toMatchObject({ status: 404 })
  })
})
