/** SEO → Rankings: each number says what it counts, the MagicBricks board shows head to head with our pages, and Google's
 * reasons a page is not indexed come with what they mean. */
import { render, screen, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import RankingsTab from '@/app/studio/seo/RankingsTab'
import type { BoardRow } from '@/lib/app/insights'

const mockRankings = jest.fn()
jest.mock('@/lib/app/insights', () => ({
  getRankings: (...a: unknown[]) => mockRankings(...a),
  revertPage: jest.fn(),
}))
jest.mock('@/lib/app/whatsapp', () => ({
  getNotifications: () => Promise.resolve({ items: [] }),
  markNotificationRead: jest.fn(),
}))

const row = (query: string, ours: number | null, magicbricks: number | null, page: string | null): BoardRow =>
  ({ query, kind: 'area', page, at: null, ours, magicbricks, acres99: null, housing: null })
const week = { at: '2026-11-06', clicks: 930, impressions: 44578, page_one: 2474, near_page_one: 357, targeted: 297, page_one_listed: 410 }
const data = {
  week: { now: week, week_ago: null },
  targets_at: null,
  doctor: { at: null, treated: [], menu: [], results: [] },
  actions: [], targets: [],
  conflicts: { at: null, total: 0, items: [] },
  gaps: { at: null, total: 0, items: [] },
  scoreboard: {
    at: '2026-11-06T06:00:00Z', searches: 300, ours: 120, magicbricks: 150, above_mb: 70, above_mb_when_shown: 30, both: 60, buyer_only: true,
    by_kind: { area: { searches: 100, ours: 40, magicbricks: 90, both: 35, ahead: 12, only_us: 5, only_mb: 55 } },
    ahead_rows: [row('flats in kharadi pune', 2, 6, '/projects/area/kharadi')],
    behind_rows: [row('2 bhk flats in wagholi pune', 7, 1, '/projects/area/wagholi/2-bhk')],
    next: [], won: [], history: [{ at: '2026-10-30', searches: 2213, ours: 574, magicbricks: 1091, above_mb: 355, above_mb_when_shown: 108 }],
    leaders: [{ site: 'housing.com', searches: 732, above_us: 650, top3: 449 }],
    area_leaders: { hinjawadi: [{ site: '99acres.com', searches: 12, above_us: 11, top3: 8 }] },
    us: { site: 'avasetu.in', searches: 1157, shows: 225, top3: 61, first: 17, place: 13, sites: 1011 },
    area_us: { hinjawadi: { site: 'avasetu.in', searches: 17, shows: 0, top3: 0, first: 0, place: 40, sites: 90 } },
  },
  coverage: { at: null, by_sitemap: [], projects: { listed: 612, inspected: 612, indexed: 364,
    missing_by_state: { 'Discovered - currently not indexed': 129, 'Excluded by ‘noindex’ tag': 73 } } },
}

beforeEach(() => mockRankings.mockResolvedValue(data))

it('says how many page-one pages are in search now and what page one counts', async () => {
  render(<RankingsTab />)
  expect(await screen.findByTestId('page-one-listed')).toHaveTextContent('410 of them are in search now; the rest are pages we took out')
  expect(screen.getByText(/average Google place is 1-10/)).toBeInTheDocument()
})

it('leads with the last 7 days and how much of them is pages in search now', async () => {
  const w = { clicks: 297, clicks_before: 496, clicks_listed: 99, clicks_listed_before: 217, impressions: 18707, impressions_before: 19903, impressions_listed: 4212, impressions_listed_before: 4863 }
  mockRankings.mockResolvedValue({ ...data, week: { now: { ...week, week: w }, week_ago: null } })
  render(<RankingsTab />)
  expect(await screen.findByText('Clicks (7 days)')).toBeInTheDocument()
  expect(screen.getByText('-199')).toBeInTheDocument()
  expect(screen.getByTestId('week-clicks-listed')).toHaveTextContent('99 (-118) on pages in search now')
  expect(screen.queryByText('Clicks (28 days)')).toBeNull()
})

it('counts MagicBricks head to head and names our page for each search', async () => {
  render(<RankingsTab />)
  expect(await screen.findByTestId('head-to-head')).toHaveTextContent(/^Above them in 30 of 60$/)   // no diff against a week that counted lookups
  expect(screen.getByText('Where we beat MagicBricks')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /\/projects\/area\/kharadi/ })).toBeInTheDocument()
  expect(screen.getByText('Where MagicBricks beats us')).toBeInTheDocument()
  expect(within(screen.getByTestId('board-kinds')).getByText('Area searches')).toBeInTheDocument()
})

it('says where we stand before naming the sites above us, overall and per area', async () => {
  render(<RankingsTab />)
  const us = await screen.findByTestId('board-us')
  expect(us).toHaveTextContent('We show in 225 of 1157 searches')
  expect(us).toHaveTextContent('Top 3 in 61, first in 17. No. 13 of the 1011 sites seen')
  expect(screen.getByText(/us 0 of 17, top 3 in 0; 99acres.com 11/)).toBeInTheDocument()
})

it("explains Google's reasons a project page is not indexed", async () => {
  render(<RankingsTab />)
  expect(await screen.findByText(/Google knows the address but has not read the page yet/)).toBeInTheDocument()
  expect(screen.getByText(/last read found the page closed to search/)).toBeInTheDocument()
})
