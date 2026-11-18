/** Studio > Results: the robots that read the site today, under the visitors (owner, 2026-11-18: "if we see in visitor it will be good"). */
import React from 'react'
import { render, screen, within } from '@testing-library/react'
import { RobotsTodayList } from '@/components/app/LiveNow'
import { getRobots, type RobotsToday } from '@/lib/app/live'

jest.mock('@/lib/app/live', () => ({ ...jest.requireActual('@/lib/app/live'), getRobots: jest.fn() }))
const mockGetRobots = getRobots as jest.MockedFunction<typeof getRobots>

const ago = (min: number) => new Date(Date.now() - min * 60_000).toISOString()
const TODAY: RobotsToday = { day: '2026-11-18', reads: 41, robots: [
  { agent: 'Google', group: 'search', reads: 34, last_at: ago(2), last_path: '/projects/kohinoor-riverdale-kharadi' },
  { agent: 'Ahrefs', group: 'seo', reads: 5, last_at: ago(40), last_path: '/' },
  { agent: 'Headless browser', group: 'script', reads: 2, last_at: ago(90), last_path: null },
] }

describe('RobotsTodayList', () => {
  it('lists each robot with what it is, its reads, when it last came and the last page', async () => {
    mockGetRobots.mockResolvedValue(TODAY)
    render(<RobotsTodayList />)
    const list = await screen.findByRole('region', { name: 'Robots today' })
    expect(within(list).getByText('Robots reading the site today (41 pages)')).toBeInTheDocument()
    const items = within(list).getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('Google · Search crawler34')
    expect(items[0]).toHaveTextContent('Kohinoor riverdale kharadi')
    expect(items[1]).toHaveTextContent('Ahrefs · SEO tool5')
    expect(items[2]).toHaveTextContent('Headless browser · Script or test browser2')
    expect(within(list).getByText(/Not counted as visitors/)).toBeInTheDocument()
  })

  it('says so when no robot came yet, and shows nothing to anyone but the owner', async () => {
    mockGetRobots.mockResolvedValue({ day: '2026-11-18', reads: 0, robots: [] })
    const { unmount } = render(<RobotsTodayList />)
    expect(await screen.findByText('No robot has read the site yet today.')).toBeInTheDocument()
    unmount()
    mockGetRobots.mockResolvedValue(null)
    const { container } = render(<RobotsTodayList />)
    await new Promise((r) => setTimeout(r, 0))
    expect(container).toBeEmptyDOMElement()
  })
})
