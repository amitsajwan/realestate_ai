import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import NewsroomPage from '@/app/studio/newsroom/page'
import {
  FIXTURE_LISTS,
  FIXTURE_QUEUE,
  FIXTURE_STATUS,
  ageLabel,
  createFixtureNewsroomApi,
  createNewsroomApi,
  normalizeItem,
  normalizeListItem,
  pillarLabel,
  tabCounts,
  whenToIso,
} from '@/lib/app/newsroom'
import type { NewsroomItem, NewsroomStatus } from '@/lib/app/newsroom'
import { ApiError } from '@/lib/app/api'

const getQueue = jest.fn()
const getStatus = jest.fn()
const approve = jest.fn()
const reject = jest.fn()
const mahareraRoundup = jest.fn()
const list = jest.fn()
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
    list: (...a: unknown[]) => list(...a),
  },
}))

const status = (over: Partial<NewsroomStatus> = {}): NewsroomStatus => ({ ...FIXTURE_STATUS, ...over })
const items = (): NewsroomItem[] => FIXTURE_QUEUE.map((i) => ({ ...i }))

beforeEach(() => {
  window.history.replaceState({}, '', '/studio/newsroom')
  ;[getQueue, getStatus, approve, reject, mahareraRoundup, list].forEach((m) => m.mockReset())
  list.mockImplementation(async (s: 'scheduled' | 'published' | 'rejected') => FIXTURE_LISTS[s].map((i) => ({ ...i })))
  getQueue.mockResolvedValue(items())
  getStatus.mockResolvedValue(status())
  approve.mockResolvedValue({})
  reject.mockResolvedValue(undefined)
})

/** Open a row (tap) and return its card. */
async function openRow(n: number) {
  const rows = await screen.findAllByTestId('queue-card')
  fireEvent.click(within(rows[n]).getAllByRole('button')[0])
  return screen.getAllByTestId('queue-card')[n]
}

describe('Newsroom screen: To review', () => {
  it('shows compact rows: title, area chips, age and the check result, closed', async () => {
    render(<NewsroomPage />)
    const rows = await screen.findAllByTestId('queue-card')
    expect(rows).toHaveLength(2)
    const r = within(rows[0])
    expect(r.getByTestId('row-title')).toHaveTextContent('Pune Metro Line 3')
    expect(r.getByText('Hinjewadi')).toBeInTheDocument()
    expect(r.getByText('Baner')).toBeInTheDocument()
    expect(r.getByText('1 day old')).toBeInTheDocument()
    expect(r.getByText('Checks passed')).toBeInTheDocument()
    expect(within(rows[1]).getByText('Needs a fix')).toBeInTheDocument()
    expect(r.getAllByRole('button')[0]).toHaveAttribute('aria-expanded', 'false')
    expect(r.queryByRole('button', { name: 'Approve' })).toBeNull()
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('opens one row at a time with the text, facts, sources and check; the text box only after Edit text', async () => {
    render(<NewsroomPage />)
    let c = within(await openRow(0))
    expect(c.getByRole('heading', { level: 2 })).toHaveTextContent('Pune Metro Line 3')
    expect(c.getByText('Infrastructure')).toBeInTheDocument()
    expect(c.getByTestId('draft-text')).toHaveTextContent('crossed 90 percent')
    expect(c.getByTestId('check-ok')).toBeInTheDocument()
    expect(c.getByText('Facts and source quotes (2)')).toBeInTheDocument()
    expect((screen.getAllByTestId('queue-card')[0].querySelector('details') as HTMLDetailsElement).open).toBe(false)
    expect(c.getByRole('link', { name: 'Times of India' })).toHaveAttribute('href', 'https://example.test/metro-line-3')
    expect(c.queryByLabelText('Post text')).toBeNull()
    fireEvent.click(c.getByRole('button', { name: 'Edit text' }))
    expect((c.getByLabelText('Post text') as HTMLTextAreaElement).value).toContain('crossed 90 percent')
    c = within(await openRow(1))
    expect(within(c.getByTestId('check-problems')).getAllByRole('listitem')).toHaveLength(3)
    expect(within(screen.getAllByTestId('queue-card')[0]).queryByRole('button', { name: 'Approve' })).toBeNull()
  })

  it('has no Approve all: each draft is approved on its own', async () => {
    render(<NewsroomPage />)
    await screen.findAllByTestId('queue-card')
    expect(screen.queryByRole('button', { name: /approve all/i })).toBeNull()
  })

  it('shows an empty state when the queue is empty', async () => {
    getQueue.mockResolvedValue([])
    render(<NewsroomPage />)
    expect(await screen.findByText(/Nothing to review right now/)).toBeInTheDocument()
    expect(screen.queryByTestId('queue-card')).toBeNull()
  })

  it('shows a clear banner when the newsroom is disabled, and the last error', async () => {
    getQueue.mockResolvedValue([])
    getStatus.mockResolvedValue(status({ enabled: false, last_error: 'Google News returned 503' }))
    render(<NewsroomPage />)
    expect(await screen.findByText(/newsroom is switched off/i)).toBeInTheDocument()
    expect(screen.getByText(/Google News returned 503/)).toBeInTheDocument()
  })

  it('shows an error with retry when the queue cannot be loaded', async () => {
    getQueue.mockRejectedValueOnce(new Error('The newsroom is only for the owner.'))
    render(<NewsroomPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('only for the owner')
    fireEvent.click(screen.getByRole('button', { name: /try again/i }))
    expect(await screen.findAllByTestId('queue-card')).toHaveLength(2)
  })

  it('approves with no body when unedited, removes the row and moves the count to Scheduled', async () => {
    render(<NewsroomPage />)
    const c = await openRow(0)
    fireEvent.click(within(c).getByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(screen.getAllByTestId('queue-card')).toHaveLength(1))
    expect(approve).toHaveBeenCalledWith('gn-metro-hinjewadi-1', {})
    expect(screen.getByRole('tab', { name: /To review/ })).toHaveTextContent('1')
    expect(screen.getByRole('tab', { name: /Scheduled/ })).toHaveTextContent('2')
  })

  it('sends edited text and flags it for re-check', async () => {
    render(<NewsroomPage />)
    const c = within(await openRow(0))
    fireEvent.click(c.getByRole('button', { name: 'Edit text' }))
    fireEvent.change(c.getByLabelText('Post text'), { target: { value: 'My own words. Thoughts?' } })
    expect(c.getByText(/Edited, will be re-checked/)).toBeInTheDocument()
    fireEvent.click(c.getByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(approve).toHaveBeenCalledWith('gn-metro-hinjewadi-1', { text: 'My own words. Thoughts?' }))
  })

  it('schedules with the picked time as an ISO string', async () => {
    render(<NewsroomPage />)
    const c = within(await openRow(0))
    fireEvent.click(c.getByRole('button', { name: 'Pick a time' }))
    fireEvent.change(c.getByLabelText(/Post at/), { target: { value: '2026-10-05T09:30' } })
    fireEvent.click(c.getByRole('button', { name: 'Approve and schedule' }))
    await waitFor(() => expect(approve).toHaveBeenCalled())
    expect(approve.mock.calls[0][1]).toEqual({ when: new Date('2026-10-05T09:30').toISOString() })
  })

  it('rejects with an optional reason after a confirm, and counts it under Rejected', async () => {
    render(<NewsroomPage />)
    const c = within(await openRow(1))
    fireEvent.click(c.getByRole('button', { name: 'Reject' }))
    expect(reject).not.toHaveBeenCalled()
    fireEvent.change(c.getByLabelText(/Reason/), { target: { value: 'old news' } })
    fireEvent.click(c.getByRole('button', { name: 'Confirm reject' }))
    await waitFor(() => expect(reject).toHaveBeenCalledWith('mr-kharadi-2', 'old news'))
    await waitFor(() => expect(screen.getAllByTestId('queue-card')).toHaveLength(1))
    expect(screen.getByRole('tab', { name: /Rejected/ })).toHaveTextContent('5')
  })

  it('rejects without a reason as undefined', async () => {
    render(<NewsroomPage />)
    const c = within(await openRow(1))
    fireEvent.click(c.getByRole('button', { name: 'Reject' }))
    fireEvent.click(c.getByRole('button', { name: 'Confirm reject' }))
    await waitFor(() => expect(reject).toHaveBeenCalledWith('mr-kharadi-2', undefined))
  })

  it('keeps the row open and shows the problem when approve fails', async () => {
    approve.mockRejectedValue(new ApiError(422, 'Check failed: date not in source'))
    render(<NewsroomPage />)
    const c = await openRow(1)
    fireEvent.click(within(c).getByRole('button', { name: 'Approve' }))
    expect(await within(screen.getAllByTestId('queue-card')[1]).findByText(/Check failed: date not in source/)).toBeInTheDocument()
    expect(screen.getAllByTestId('queue-card')).toHaveLength(2)
    expect(within(screen.getAllByTestId('queue-card')[1]).getByRole('button', { name: 'Approve' })).toBeEnabled()
  })
})

describe('Newsroom screen: tabs', () => {
  it('shows the four tabs with counts from the status call; To review is gold and the default', async () => {
    render(<NewsroomPage />)
    await screen.findAllByTestId('queue-card')
    const tabs = screen.getAllByRole('tab')
    expect(tabs.map((t) => t.textContent)).toEqual(['To review2', 'Scheduled1', 'Published7', 'Rejected4'])
    expect(tabs[0]).toHaveAttribute('aria-selected', 'true')
    expect(tabs[0].querySelector('span')?.className).toContain('bg-[#f0b440]')
    expect(screen.queryByTestId('count-published')).toBeNull()
    expect(list).not.toHaveBeenCalled()
  })

  it('opens Published from the tab, keeps it in the address and shows each channel link, the news page and the time', async () => {
    render(<NewsroomPage />)
    await screen.findAllByTestId('queue-card')
    fireEvent.click(screen.getByRole('tab', { name: /Published/ }))
    expect(window.location.search).toBe('?tab=published')
    const row = within(await screen.findByTestId('list-row'))
    expect(list).toHaveBeenCalledWith('published', 50)
    expect(row.getByTestId('row-title')).toHaveTextContent('Kharadi-Mundhwa bridge')
    expect(row.getByText('Posted')).toBeInTheDocument()
    expect(row.getByTestId('row-time')).toHaveAttribute('dateTime', FIXTURE_LISTS.published[0].published_at)
    expect(row.getByRole('link', { name: /^Facebook/ })).toHaveAttribute('href', 'https://www.facebook.com/example/posts/1')
    expect(row.getByRole('link', { name: /^Instagram/ })).toHaveAttribute('href', 'https://www.instagram.com/p/example1/')
    expect(row.getByRole('link', { name: /^News page/ })).toHaveAttribute('href', expect.stringContaining('/news/kharadi-mundhwa-bridge'))
    expect(screen.queryByTestId('queue-card')).toBeNull()
  })

  it('lands on the tab named in the address', async () => {
    window.history.replaceState({}, '', '/studio/newsroom?tab=rejected')
    render(<NewsroomPage />)
    const row = within(await screen.findByTestId('list-row'))
    expect(screen.getByRole('tab', { name: /Rejected/ })).toHaveAttribute('aria-selected', 'true')
    expect(row.getByText('Rejected')).toBeInTheDocument()
    expect(row.getByTestId('row-reason')).toHaveTextContent('Reason: old news')
    expect(row.queryByRole('link')).toBeNull()
  })

  it('shows Scheduled with its time and an empty state when a list is empty', async () => {
    render(<NewsroomPage />)
    await screen.findAllByTestId('queue-card')
    fireEvent.click(screen.getByRole('tab', { name: /Scheduled/ }))
    const row = within(await screen.findByTestId('list-row'))
    expect(row.getByText('Goes out')).toBeInTheDocument()
    expect(row.getByTestId('row-time')).toBeInTheDocument()
    list.mockResolvedValueOnce([])
    fireEvent.click(screen.getByRole('tab', { name: /Published/ }))
    expect(await screen.findByText('Nothing posted yet.')).toBeInTheDocument()
  })
})

describe('MahaRERA post button (in the title)', () => {
  const button = () => screen.findByRole('button', { name: '+ MahaRERA post' })

  it('queues the post with one click, goes to To review and reloads it', async () => {
    window.history.replaceState({}, '', '/studio/newsroom?tab=published')
    mahareraRoundup.mockResolvedValue({ id: 'maharera-1', created: true, projects: 4 })
    render(<NewsroomPage />)
    fireEvent.click(await button())
    expect(await screen.findByRole('status')).toHaveTextContent('MahaRERA post added to To review (4 projects).')
    expect(mahareraRoundup).toHaveBeenCalledTimes(1)
    await waitFor(() => expect(getQueue).toHaveBeenCalledTimes(2))
    expect(screen.getByRole('tab', { name: /To review/ })).toHaveAttribute('aria-selected', 'true')
  })

  it('says so when one is already waiting', async () => {
    mahareraRoundup.mockResolvedValue({ id: 'maharera-1', created: false, projects: 4 })
    render(<NewsroomPage />)
    fireEvent.click(await button())
    expect(await screen.findByRole('status')).toHaveTextContent('A MahaRERA post is already waiting in To review.')
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
    await api.list('published', 20)
    const calls = f.mock.calls.map((c) => [c[0], c[1].method, c[1].body, c[1].headers.Authorization])
    expect(calls).toEqual([
      ['http://x/api/v1/newsroom/queue', 'GET', undefined, 'Bearer abc'],
      ['http://x/api/v1/newsroom/status', 'GET', undefined, 'Bearer abc'],
      ['http://x/api/v1/newsroom/items/i%201/approve', 'POST', JSON.stringify({ text: 'hi', when: '2026-10-05T04:00:00.000Z' }), 'Bearer abc'],
      ['http://x/api/v1/newsroom/items/i1/reject', 'POST', JSON.stringify({ reason: 'old' }), 'Bearer abc'],
      ['http://x/api/v1/newsroom/items/i2/reject', 'POST', '{}', 'Bearer abc'],
      ['http://x/api/v1/newsroom/maharera-roundup', 'POST', undefined, 'Bearer abc'],
      ['http://x/api/v1/newsroom/items?status=published&limit=20', 'GET', undefined, 'Bearer abc'],
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

  it('normalizes list rows and counts tabs (approved counts as Scheduled)', () => {
    const n = normalizeListItem({ id: 'a', title: 'T', status: 'published', permalinks: { facebook: 'https://fb.test/1', instagram: 'javascript:x' },
      news_url: 'https://site.test/news/t-a', published_at: '2026-10-06T10:00:00+00:00' })
    expect(n.permalinks).toEqual({ facebook: 'https://fb.test/1', instagram: undefined })
    expect(n.news_url).toBe('https://site.test/news/t-a')
    expect(n.reason).toBeNull()
    expect(normalizeListItem(null)).toMatchObject({ id: '', areas: [], check: null, news_url: null })
    expect(tabCounts({ pending_review: 3, approved: 2, scheduled: 1, published: 7 })).toEqual({ review: 3, scheduled: 3, published: 7, rejected: 0 })
  })

  it('formats labels and dates', () => {
    expect(pillarLabel('rules_money')).toBe('Rules and money')
    expect(pillarLabel('some_new_one')).toBe('Some new one')
    expect(ageLabel(0)).toBe('today')
    expect(ageLabel(4)).toBe('4 days old')
    expect(whenToIso('')).toBeUndefined()
    expect(whenToIso('nope')).toBeUndefined()
  })

  it('fixture api lists handled items by status', async () => {
    const f = createFixtureNewsroomApi()
    expect((await f.list('published'))[0].permalinks.facebook).toMatch(/^https:/)
    expect((await f.list('rejected'))[0].reason).toBe('old news')
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
