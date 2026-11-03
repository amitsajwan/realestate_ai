/** Studio > Results "Right now" and "Today on the site" (docs/plan/site-live-presence.md D2). */
import React from 'react'
import { act, fireEvent, render, screen, within } from '@testing-library/react'
import LiveNow from '@/components/app/LiveNow'
import { aboutLine, getLive, pageLabel, readTime, type Live, type LiveStory } from '@/lib/app/live'

jest.mock('@/lib/app/live', () => ({ ...jest.requireActual('@/lib/app/live'), getLive: jest.fn() }))
const mockGetLive = getLive as jest.MockedFunction<typeof getLive>

const TODAY = { date: '2026-10-26', visitors: 4, visits: 5, pages: 9, one_page_visits: 2, avg_read_s: 75,
  top_pages: [{ page: '/projects/godrej-ivara-pune', views: 3, avg_read_s: 95 }], left_from: [{ page: '/guides/upper-kharadi', visits: 2 }], stories: [] as LiveStory[] }

const LIVE: Live = {
  as_of: '2026-10-26T10:00:00',
  now: {
    count: 2,
    visitors: [
      { who: { kind: 'visitor', label: 'Visitor 3' }, page: '/projects/lodha-camelot', reading: true, pages: 2, minutes: 4, came_from: 'instagram',
        device: 'Android phone · Chrome', area: 'Pune, Maharashtra', network: 'Jio',
        journey: [{ page: '/projects/godrej-ivara-pune', at: '15:26', read_s: 80 }, { page: '/projects/lodha-camelot', at: '15:29', read_s: 40 }] },
      { who: { kind: 'lead', label: 'Rahul T', lead_id: 'C1' }, page: '/', reading: false, pages: 1, minutes: 0, came_from: 'direct', journey: [{ page: '/', at: '15:30', read_s: null }] },
    ],
  },
  today: TODAY,
}

test('page paths read as plain names', () => {
  expect(pageLabel('/')).toBe('Home page')
  expect(pageLabel('/projects/godrej-ivara-pune?src=ig')).toBe('Project: Godrej ivara pune')
  expect(pageLabel('/projects/area/upper-kharadi/2-bhk')).toBe('Projects in Upper kharadi (2 bhk)')
  expect(pageLabel('/guides/mhada-pune-lottery')).toBe('Guide: Mhada pune lottery')
  expect(pageLabel('/news/track/pune-metro-line-3')).toBe('Tracker: Pune metro line 3')
  expect(pageLabel('/news/abc123')).toBe('News story')
  expect(pageLabel('/agent/house-deal/projects/gulmohar-city')).toBe('Project: Gulmohar city')
  expect(pageLabel('/agent/house-deal')).toBe('Agent home page')
  expect(pageLabel('/2-bhk/kharadi')).toBe('/2-bhk/kharadi')
})

test('reading time reads in minutes and seconds', () => {
  expect([readTime(40), readTime(60), readTime(75), readTime(0), readTime(null)]).toEqual(['40s', '1m', '1m 15s', '', ''])
})

test('shows who is here now, busiest first, and opens one visitor\'s pages', async () => {
  mockGetLive.mockResolvedValue(LIVE)
  await act(async () => { render(<LiveNow />) })
  expect(screen.getByText('2 people are on the site. Tap one to see the pages they read.')).toBeInTheDocument()
  expect(screen.getByText('Project: Lodha camelot')).toBeInTheDocument()
  expect(screen.getByText(/Visitor 3 · 2 pages · 4 min · from Instagram/)).toBeInTheDocument()
  expect(screen.getByText(/Rahul T · 1 page · just came · from Direct · tab open/)).toBeInTheDocument()
  expect(screen.getByText('Android phone · Chrome · Pune approx. · Jio')).toBeInTheDocument()

  fireEvent.click(screen.getByText('Project: Lodha camelot'))
  const now = within(screen.getByRole('region', { name: 'Right now' }))
  expect(now.getByRole('link', { name: 'Project: Godrej ivara pune' })).toHaveAttribute('href', '/projects/godrej-ivara-pune')
  expect(screen.getByText('1m 20s')).toBeInTheDocument()
  fireEvent.click(screen.getByText('Home page'))
  expect(screen.getByRole('link', { name: 'Open lead' })).toHaveAttribute('href', '/studio/leads/C1')
})

test('shows today\'s reading: visitors, pages, time per page, most read and where people left', async () => {
  mockGetLive.mockResolvedValue(LIVE)
  await act(async () => { render(<LiveNow />) })
  expect(screen.getByText('1m 15s')).toBeInTheDocument()
  expect(screen.getByText('2 of 5 visits read only one page.')).toBeInTheDocument()
  expect(screen.getByText('1m 35s')).toBeInTheDocument()
  expect(screen.getByText('Most left from: Guide: Upper kharadi (2)')).toBeInTheDocument()
})

test('an empty site says so plainly', async () => {
  mockGetLive.mockResolvedValue({ ...LIVE, now: { count: 0, visitors: [] }, today: { ...TODAY, visits: 0, top_pages: [], left_from: [] } })
  await act(async () => { render(<LiveNow />) })
  expect(screen.getByText('Nobody else is on the site this minute.')).toBeInTheDocument()
})

test('refreshes every 15 seconds and keeps the last numbers when a refresh fails', async () => {
  jest.useFakeTimers()
  try {
    mockGetLive.mockReset()
    mockGetLive.mockResolvedValueOnce(LIVE).mockRejectedValueOnce(new Error('offline'))
    await act(async () => { render(<LiveNow />) })
    await act(async () => { jest.advanceTimersByTime(15_000) })
    expect(mockGetLive).toHaveBeenCalledTimes(2)
    expect(screen.getByText('Project: Lodha camelot')).toBeInTheDocument()
    expect(screen.getByText('Last refresh failed; showing the numbers from before.')).toBeInTheDocument()
  } finally {
    jest.useRealTimers()
  }
})

const STORY: LiveStory = {
  who: { kind: 'visitor', label: 'Visitor 6' }, start: '00:38', end: '00:45', minutes: 7, here_now: false, came_from: 'chatgpt',
  landing: '/agents', device: 'Windows computer · Chrome', area: 'Bengaluru, Karnataka', network: 'Airtel', pages: 2, read_s: 75,
  steps: [{ page: '/agents', at: '00:38', read_s: 30 }, { page: '/trial', at: '00:40', read_s: 45 }],
  did: [{ what: 'Opened the chat', at: '00:41' }],
}

test('the device line leaves out what is not known', () => {
  expect(aboutLine({ device: 'iPhone · Safari', area: null, network: 'Jio' })).toBe('iPhone · Safari · Jio')
  expect(aboutLine({})).toBe('')
})

test("today's visitors tell each visit: when, from where, on what, and what they did", async () => {
  mockGetLive.mockResolvedValue({ ...LIVE, today: { ...TODAY, stories: [STORY] } })
  await act(async () => { render(<LiveNow />) })
  const list = within(screen.getByRole('region', { name: "Today's visitors" }))
  expect(list.getByText('00:38–00:45')).toBeInTheDocument()
  expect(list.getByText(/Visitor 6 · from ChatGPT/)).toBeInTheDocument()
  expect(list.getByText('2 pages · read 1m 15s · first: Agents list')).toBeInTheDocument()
  expect(list.getByText('Windows computer · Chrome · Bengaluru approx. · Airtel')).toBeInTheDocument()
  expect(list.getByText('Opened the chat')).toBeInTheDocument()
  fireEvent.click(list.getByText(/Visitor 6 · from ChatGPT/))
  expect(list.getByRole('link', { name: 'Free trial (agents)' })).toHaveAttribute('href', '/trial')
  expect(list.getByRole('link', { name: 'IP Geolocation by DB-IP' })).toHaveAttribute('href', 'https://db-ip.com')
})

test('your own browser is listed as You but the count says nobody else is here', async () => {
  const me = { ...LIVE.now.visitors[1], who: { kind: 'you' as const, label: 'You' } }
  mockGetLive.mockResolvedValue({ ...LIVE, now: { count: 0, visitors: [me] } })
  await act(async () => { render(<LiveNow />) })
  expect(screen.getByText('Nobody else is on the site this minute.')).toBeInTheDocument()
  expect(screen.getByText(/You · 1 page/)).toBeInTheDocument()
  expect(screen.getByText('"You" is a browser signed in to Studio: shown, never counted.')).toBeInTheDocument()
})
