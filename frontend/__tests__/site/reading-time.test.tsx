/** Reading pings and one view per page (docs/plan/site-live-presence.md D1). */
import React from 'react'
import { render } from '@testing-library/react'
import TrackingBeacon from '@/components/site/TrackingBeacon'
import { MAX_PINGS, PING_EVERY_MS, startReading } from '@/lib/site/tracking'

let mockPath = '/projects/godrej-ivara-pune'
jest.mock('next/navigation', () => ({ usePathname: () => mockPath }))

let visibility: DocumentVisibilityState = 'visible'
const fetchMock = jest.fn((..._args: unknown[]) => Promise.resolve({ ok: true }))

beforeAll(() => {
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => visibility })
})

beforeEach(() => {
  jest.useFakeTimers()
  visibility = 'visible'
  fetchMock.mockClear()
  ;(global as unknown as { fetch: unknown }).fetch = fetchMock
})

afterEach(() => {
  jest.useRealTimers()
})

const sent = (route: string) =>
  fetchMock.mock.calls
    .filter((c) => String(c[0]).endsWith('/t/' + route))
    .map((c) => JSON.parse((c[1] as { body: string }).body))

const pings = () => sent('ping').map((b) => b.seconds)

function setVisibility(v: DocumentVisibilityState) {
  visibility = v
  document.dispatchEvent(new Event('visibilitychange'))
}

test('a 404 page is not a view: a guessed address does not show as a visitor', () => {
  render(<><div data-page-not-found /><TrackingBeacon agentSlug="avasetu" /></>)
  expect(sent('event')).toEqual([])
})

test('pings the seconds the page was visible every 30 s and once more when it is left', () => {
  const stop = startReading('avasetu', 'view00000001')
  jest.advanceTimersByTime(PING_EVERY_MS)
  jest.advanceTimersByTime(PING_EVERY_MS)
  jest.advanceTimersByTime(10_000)
  stop()
  expect(pings()).toEqual([30, 60, 70])
  expect(sent('ping')[0]).toMatchObject({ agent_slug: 'avasetu', view_id: 'view00000001' })
})

test('a hidden tab is not reading', () => {
  const stop = startReading('avasetu', 'view00000002')
  jest.advanceTimersByTime(10_000)
  setVisibility('hidden') // tells the server at once: the visitor may never come back
  jest.advanceTimersByTime(60_000)
  setVisibility('visible')
  jest.advanceTimersByTime(20_000)
  stop()
  expect(pings()).toEqual([10, 30])
})

test('a page left at once sends no ping, and leaving twice sends one', () => {
  const stop = startReading('avasetu', 'view00000003')
  stop()
  expect(pings()).toEqual([])
  const again = startReading('avasetu', 'view00000004')
  jest.advanceTimersByTime(5_000)
  window.dispatchEvent(new Event('pagehide'))
  again()
  expect(pings()).toEqual([5])
})

test('a tab left open all day stops pinging', () => {
  const stop = startReading('avasetu', 'view00000005')
  jest.advanceTimersByTime(PING_EVERY_MS * (MAX_PINGS + 20))
  stop()
  expect(pings()).toHaveLength(MAX_PINGS)
})

test('each page path is its own view with its own id', () => {
  mockPath = '/projects/godrej-ivara-pune'
  const { rerender, unmount } = render(<TrackingBeacon agentSlug="avasetu" />)
  mockPath = '/projects/lodha-camelot'
  rerender(<TrackingBeacon agentSlug="avasetu" />)
  unmount()
  const views = sent('event')
  expect(views.map((v) => v.type)).toEqual(['page_view', 'page_view'])
  expect(views[0].view_id).toMatch(/^[a-z0-9]{24}$/)
  expect(views[0].view_id).not.toEqual(views[1].view_id)
})

test('a browser signed in to Studio marks its views as staff, others do not', () => {
  const { unmount } = render(<TrackingBeacon agentSlug="avasetu" />)
  unmount()
  window.localStorage.setItem('app_token', 'studio-token')
  try {
    const again = render(<TrackingBeacon agentSlug="avasetu" />)
    again.unmount()
  } finally {
    window.localStorage.removeItem('app_token')
  }
  expect(sent('event').map((v) => v.staff)).toEqual([undefined, true])
})
