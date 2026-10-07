import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { AppShell, countWaitingPosts } from '@/components/app/AppShell'

let mockOwner = true
let mockPath = '/studio/admin'
const mockUpcoming = jest.fn()
const mockStatus = jest.fn()
jest.mock('next/navigation', () => ({ usePathname: () => mockPath }))
jest.mock('@/lib/app/client', () => ({ isFixtureMode: () => false }))
jest.mock('@/components/app/agents/useIsOwner', () => ({ useIsOwner: () => mockOwner }))
jest.mock('@/lib/app/content', () => ({ contentApi: { getUpcoming: (...a: unknown[]) => mockUpcoming(...a) } }))
jest.mock('@/lib/app/newsroom', () => ({ newsroomApi: { getStatus: (...a: unknown[]) => mockStatus(...a) } }))

const planned = (slug: string, channel = 'instagram') => ({ id: `${slug}-${channel}`, slug, channel, status: 'planned' })
const nav = () => within(screen.getByRole('navigation', { name: 'Main' }))
const contentLink = () => nav().getByRole('link', { name: /Content/ })
const newsroomLink = () => nav().getByRole('link', { name: /Newsroom/ })

beforeEach(() => {
  mockOwner = true
  mockPath = '/studio/admin'
  mockUpcoming.mockReset().mockResolvedValue([])
  mockStatus.mockReset().mockResolvedValue({ enabled: true, counts: { pending_review: 0 }, last_run_at: null, last_error: null })
})

describe('AppShell tabs', () => {
  it('owners get five items: Home, Content, Newsroom, Leads, More, with 12 px labels', async () => {
    render(<AppShell><p>x</p></AppShell>)
    const links = nav().getAllByRole('link')
    expect(links.map((l) => l.getAttribute('href'))).toEqual(['/studio', '/studio/content', '/studio/newsroom', '/studio/leads'])
    const more = nav().getByRole('button', { name: 'More' })
    expect(nav().getAllByRole('listitem')).toHaveLength(5)
    for (const el of [...links, more]) {
      expect(el.className).toContain('text-xs')
      expect(el.className).toContain('min-h-[60px]')
      expect(el.className).not.toContain('text-[10px]')
    }
    await waitFor(() => expect(mockStatus).toHaveBeenCalled())
  })

  it('More opens a sheet with the rest; a page inside More lights up the More tab', async () => {
    render(<AppShell><p>x</p></AppShell>)
    const more = nav().getByRole('button', { name: 'More' })
    expect(more).toHaveAttribute('aria-current', 'page')
    expect(more.className).toContain('text-[#0f2340]')
    expect(nav().getAllByRole('link').every((l) => !l.hasAttribute('aria-current'))).toBe(true)
    fireEvent.click(more)
    const sheet = screen.getByRole('dialog', { name: 'More' })
    const rows = within(sheet).getAllByRole('link')
    expect(rows.map((l) => l.getAttribute('href'))).toEqual(['/studio/listings', '/studio/interest', '/studio/agents', '/studio/admin', '/studio/profile'])
    expect(rows[3]).toHaveAttribute('aria-current', 'page')
    expect(rows[0].className).toContain('min-h-[56px]')
    fireEvent.click(within(sheet).getByRole('button', { name: 'Close' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    await waitFor(() => expect(mockStatus).toHaveBeenCalled())
  })

  it('a daily page lights its own tab, not More', async () => {
    mockPath = '/studio/content'
    render(<AppShell><p>x</p></AppShell>)
    expect(contentLink()).toHaveAttribute('aria-current', 'page')
    expect(nav().getByRole('button', { name: 'More' })).not.toHaveAttribute('aria-current')
    await waitFor(() => expect(mockStatus).toHaveBeenCalled())
  })

  it('everyone else keeps the six tabs at the normal size, no More and no badge calls', () => {
    mockOwner = false
    mockPath = '/studio/listings'
    render(<AppShell><p>x</p></AppShell>)
    const links = nav().getAllByRole('link')
    expect(links.map((l) => l.getAttribute('href'))).toEqual([
      '/studio', '/studio/listings', '/studio/interest', '/studio/newsroom', '/studio/content', '/studio/leads',
    ])
    expect(links[0].className).toContain('text-xs')
    expect(links[1]).toHaveAttribute('aria-current', 'page')
    expect(nav().queryByRole('button', { name: 'More' })).toBeNull()
    expect(mockUpcoming).not.toHaveBeenCalled()
    expect(mockStatus).not.toHaveBeenCalled()
  })
})

describe('AppShell badges', () => {
  it('Content counts waiting posts once per slug; Newsroom shows drafts waiting for review', async () => {
    mockUpcoming.mockResolvedValue([planned('a'), planned('a', 'facebook_page'), planned('b'), { ...planned('c'), status: 'approved' }])
    mockStatus.mockResolvedValue({ enabled: true, counts: { pending_review: 3 }, last_run_at: null, last_error: null })
    render(<AppShell><p>x</p></AppShell>)
    await waitFor(() => expect(within(contentLink()).getByTestId('nav-badge')).toHaveTextContent('2'))
    expect(within(newsroomLink()).getByTestId('nav-badge')).toHaveTextContent('3')
    expect(within(contentLink()).getByTestId('nav-badge').className).toContain('bg-[#f0b440]')
  })

  it('caps at 9+ and hides at 0', async () => {
    mockUpcoming.mockResolvedValue(Array.from({ length: 12 }, (_, i) => planned(`p${i}`)))
    mockStatus.mockResolvedValue({ enabled: true, counts: { pending_review: 0 }, last_run_at: null, last_error: null })
    render(<AppShell><p>x</p></AppShell>)
    await waitFor(() => expect(within(contentLink()).getByTestId('nav-badge')).toHaveTextContent('9+'))
    expect(within(newsroomLink()).queryByTestId('nav-badge')).toBeNull()
  })

  it('a failed call shows no badge and the bar still renders', async () => {
    mockUpcoming.mockRejectedValue(new Error('down'))
    mockStatus.mockResolvedValue({ enabled: true, counts: { pending_review: 4 }, last_run_at: null, last_error: null })
    render(<AppShell><p>x</p></AppShell>)
    await waitFor(() => expect(within(newsroomLink()).getByTestId('nav-badge')).toHaveTextContent('4'))
    expect(within(contentLink()).queryByTestId('nav-badge')).toBeNull()
    expect(nav().getAllByRole('listitem')).toHaveLength(5)
  })

  it('asks again when the app comes back to the front', async () => {
    render(<AppShell><p>x</p></AppShell>)
    await waitFor(() => expect(mockUpcoming).toHaveBeenCalledTimes(1))
    mockStatus.mockResolvedValue({ enabled: true, counts: { pending_review: 1 }, last_run_at: null, last_error: null })
    await act(async () => { document.dispatchEvent(new Event('visibilitychange')) })
    await waitFor(() => expect(within(newsroomLink()).getByTestId('nav-badge')).toHaveTextContent('1'))
    expect(mockUpcoming).toHaveBeenCalledTimes(2)
  })

  it('countWaitingPosts counts distinct planned slugs', () => {
    expect(countWaitingPosts([planned('a'), planned('a', 'facebook_page'), { ...planned('b'), status: 'published' }])).toBe(1)
    expect(countWaitingPosts([])).toBe(0)
  })
})
