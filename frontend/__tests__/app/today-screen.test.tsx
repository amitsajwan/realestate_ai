import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { TodayScreen } from '@/components/app/home/TodayScreen'
import { createFixtureApi } from '@/lib/app/fixtures'
import { callList, setupSteps, todoRows } from '@/lib/app/home'
import type { AppApi, BusinessToday, Lead } from '@/lib/app/types'

let fx: AppApi
const getToday = jest.fn()
const listListings = jest.fn()
const threads = jest.fn()
const getNotifications = jest.fn()
const getUpcoming = jest.fn()
const loadBrand = jest.fn()
const updateLead = jest.fn()
let mockOwner = false
jest.mock('@/lib/app/client', () => ({
  api: {
    getToday: () => getToday(),
    listLeads: () => fx.listLeads(),
    listListings: () => listListings(),
    getWeeklyReport: () => fx.getWeeklyReport(),
    updateLead: (...a: unknown[]) => updateLead(...a),
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
jest.mock('@/lib/app/inbox', () => ({ inboxApi: { threads: () => threads() } }))
jest.mock('@/lib/app/whatsapp', () => ({ getNotifications: () => getNotifications() }))
jest.mock('@/lib/app/content', () => ({ contentApi: { getUpcoming: () => getUpcoming() } }))
jest.mock('@/lib/app/branding', () => ({ brandingApi: { load: () => loadBrand() }, assetUrl: (u: string) => u }))
jest.mock('@/lib/app/session', () => ({ getSiteUrl: () => 'https://example.test/agent/amit' }))
jest.mock('@/components/app/agents/useIsOwner', () => ({ useIsOwner: () => mockOwner }))
jest.mock('@/components/app/AppShell', () => ({ countWaitingPosts: (x: unknown[]) => x.length }))

const brand = (over: Record<string, unknown> = {}) => ({
  slug: 'amit', agent_name: 'Amit Sajwan', branding_data: { logo: '/l.png', rera_agent_no: 'A5210001' }, rera_due_at: null, ...over,
})
const note = (kind: string) => ({ id: kind + Math.random(), kind, summary: '', ref: {}, created_at: '', read: false })

beforeEach(() => {
  fx = createFixtureApi({ getItem: () => null, setItem: () => undefined })
  mockOwner = false
  getToday.mockReset().mockImplementation(() => fx.getToday())
  listListings.mockReset().mockImplementation(() => fx.listListings())
  threads.mockReset().mockResolvedValue([])
  getNotifications.mockReset().mockResolvedValue({ items: [], unread: 0 })
  getUpcoming.mockReset().mockResolvedValue([])
  loadBrand.mockReset().mockResolvedValue(brand())
  updateLead.mockReset().mockResolvedValue({})
  try { window.localStorage.clear() } catch { /* ignore */ }
})

describe('Studio home', () => {
  it('greets the agent by first name and puts Add listing and Share my website on top', async () => {
    render(<TodayScreen />)
    expect(await screen.findByRole('heading', { level: 1, name: /, Amit$/ })).toBeInTheDocument()
    expect(screen.getByTestId('quick-add-listing')).toHaveAttribute('href', '/studio/listings/new')
    expect(screen.getByTestId('quick-share-site').getAttribute('href')).toContain(encodeURIComponent('https://example.test/agent/amit'))
    expect(screen.getByRole('link', { name: 'My brand and website' })).toHaveAttribute('href', '/studio/profile')
  })

  it('lists each person to call once, the overdue first, with Call and WhatsApp on the row', async () => {
    render(<TodayScreen />)
    const list = await screen.findByRole('region', { name: 'Call today' })
    const names = within(list).getAllByTestId('call-row').map((r) => within(r).getAllByRole('link')[0].textContent)
    // Sneha is overdue; Rohit is the AI's hot pick and also a hot buyer; Priya is due today and also hot: each appears once
    expect(names.map((n) => n?.split(/Overdue|Hot|Today/)[0])).toEqual(['Sneha Kulkarni', 'Rohit Deshmukh', 'Priya Nair'])
    expect(within(list).getByRole('link', { name: 'Call Priya Nair' })).toHaveAttribute('href', 'tel:+919811223344')
    expect(within(list).getByRole('link', { name: 'WhatsApp Rohit Deshmukh' }).getAttribute('href')).toMatch(/^https:\/\/wa\.me\/919822012345\?text=Hi%20Rohit/)
    expect(within(list).getAllByTestId('call-row')[0]).toHaveTextContent('Overdue')
  })

  it('after Call, home asks how it went and logs it on the lead', async () => {
    render(<TodayScreen />)
    const list = await screen.findByRole('region', { name: 'Call today' })
    fireEvent.click(within(list).getByRole('link', { name: 'Call Rohit Deshmukh' }))
    const log = screen.getByRole('region', { name: 'Log the call' })
    expect(log).toHaveTextContent('Called Rohit? How did it go?')
    fireEvent.click(within(log).getByRole('button', { name: 'No answer' }))
    await waitFor(() => expect(updateLead).toHaveBeenCalledWith('c1', { call: 'no_answer' }))
    await waitFor(() => expect(screen.queryByRole('region', { name: 'Log the call' })).toBeNull())
  })

  it('Not now closes the call log without touching the lead', async () => {
    render(<TodayScreen />)
    const list = await screen.findByRole('region', { name: 'Call today' })
    fireEvent.click(within(list).getByRole('link', { name: 'Call Priya Nair' }))
    fireEvent.click(screen.getByRole('button', { name: 'Not now' }))
    expect(screen.queryByRole('region', { name: 'Log the call' })).toBeNull()
    expect(updateLead).not.toHaveBeenCalled()
  })

  it('folds listings to confirm and marketing nudges into single to-do rows, each opening its list', async () => {
    render(<TodayScreen />)
    const confirm = await screen.findByTestId('todo-freshness')
    expect(confirm).toHaveTextContent('2listings to confirm as still available (1 hidden from buyers)')
    expect(confirm).toHaveAttribute('href', '/studio/listings?tab=needs')
    expect(screen.getAllByTestId('todo-marketing')).toHaveLength(1)
    expect(screen.queryByText(/AI recommends/)).toBeNull()
    expect(screen.queryByRole('button', { name: /Create marketing/ })).toBeNull()
  })

  it('agents never ask for posts; the owner sees posts, join requests and passed buyers', async () => {
    const { unmount } = render(<TodayScreen />)
    await screen.findByRole('region', { name: 'Call today' })
    expect(getUpcoming).not.toHaveBeenCalled()
    unmount()

    mockOwner = true
    getUpcoming.mockResolvedValue([{}, {}, {}])
    getNotifications.mockResolvedValue({ items: [note('invite_request'), note('buyer_passed'), note('new_chat_lead')], unread: 3 })
    threads.mockResolvedValue([{ needs_you: true }, { needs_you: false }])
    render(<TodayScreen />)
    expect(await screen.findByTestId('todo-posts')).toHaveTextContent('3posts waiting for your OK')
    expect(screen.getByTestId('todo-invites')).toHaveAttribute('href', '/studio/admin')
    expect(screen.getByTestId('todo-passed')).toHaveTextContent('1buyer was passed to you')
    expect(screen.getByTestId('todo-inbox')).toHaveAttribute('href', '/studio/inbox?tab=needs')
  })

  it('a new agent gets the setup steps and an all-caught-up note instead of empty lists', async () => {
    getToday.mockResolvedValue({ counts: { new_enquiries_24h: 0, hot: 0, site_visits: 0, follow_ups_due: 0, uncontacted: 0 }, hot_buyers: [], follow_ups: [], headline: '' })
    listListings.mockResolvedValue([])
    jest.spyOn(fx, 'listLeads').mockResolvedValue([])
    loadBrand.mockResolvedValue(brand({ branding_data: {} }))
    render(<TodayScreen />)
    const setup = await screen.findByRole('region', { name: 'Get set up' })
    expect(setup).toHaveTextContent('0 of 4 done')
    expect(within(setup).getByTestId('setup-listing')).toHaveAttribute('href', '/studio/listings/new')
    expect(screen.getByRole('region', { name: 'All caught up' })).toHaveTextContent('Add your first listing')
    expect(screen.queryByRole('region', { name: 'Call today' })).toBeNull()
  })

  it('with a RERA date set, the dated reminder shows and the setup list leaves that step out', async () => {
    loadBrand.mockResolvedValue(brand({ branding_data: {}, rera_due_at: '2099-01-10T00:00:00Z' }))
    render(<TodayScreen />)
    expect(await screen.findByTestId('rera-reminder')).toHaveTextContent('Add your MahaRERA agent number by')
    expect(screen.queryByTestId('setup-rera')).toBeNull()
  })

  it('the day summary failing shows a retry, and the rest of home still shows', async () => {
    getToday.mockRejectedValue(new Error('Cannot reach the server'))
    render(<TodayScreen />)
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Cannot reach the server'))
    expect(screen.getByTestId('todo-freshness')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })

  it('listings that cannot be loaded leave the confirm row out, never an error', async () => {
    listListings.mockRejectedValue(new Error('boom'))
    render(<TodayScreen />)
    await screen.findByRole('region', { name: 'Call today' })
    expect(screen.queryByTestId('todo-freshness')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})

describe('home rules', () => {
  const lead = (id: string, over: Partial<Lead> = {}): Lead =>
    ({ id, name: id.toUpperCase(), phone: '+91980000000' + id.length, stage: 'new', temperature: 'warm', score: 1, ...over }) as Lead
  const day = (over: Partial<BusinessToday> = {}) => ({ follow_ups: [], hot_buyers: [], actions: [], ...over })

  it('callList puts unanswered leads before today\'s follow-ups, longest waiting first, and skips closed leads', () => {
    const leads = [
      lead('a', { contact: { state: 'not_contacted', at: '2026-10-27T09:00:00Z' } as Lead['contact'] }),
      lead('b', { contact: { state: 'waiting_you', at: '2026-10-26T09:00:00Z', channel: 'whatsapp' } as Lead['contact'] }),
      lead('c', { stage: 'won' }),
    ]
    const today = day({
      follow_ups: [{ id: 'd', name: 'D', phone: '1', due_at: '2026-10-27T10:00:00Z', overdue: false, reason: 'Call back' }],
      hot_buyers: [{ id: 'c', name: 'C', phone: '2', score: 90, temperature: 'hot', requirement_line: null, top_match: null }],
    })
    const out = callList(today, leads, new Date('2026-10-27T12:00:00Z'))
    expect(out.map((x) => x.id)).toEqual(['b', 'a', 'd'])
    expect(out[0].tone).toBe('bad')   // over a day waiting
    expect(out[2].why).toBe('Today: Call back')
  })

  it('callList takes the phone from the leads list when the action has none', () => {
    const out = callList(day({ actions: [{ type: 'call', title: 'Call A', detail: 'hot buyer', priority: 1, lead_id: 'a' }] }), [lead('a')])
    expect(out).toEqual([{ id: 'a', name: 'A', phone: '+919800000001', why: 'hot buyer', tone: 'hot' }])
  })

  it('todoRows folds one marketing nudge to its listing and several to the live listings', () => {
    const zero = { inbox: 0, passed: 0, posts: 0, invites: 0, trials: 0, seo: 0, photos: 0, freshness: 0 }
    const m = (id: string) => ({ type: 'create_marketing' as const, title: `Start marketing for ${id}`, detail: '', priority: 3 as const, listing_id: id })
    expect(todoRows(zero, [m('x')])).toEqual([{ key: 'marketing', href: '/studio/listings/x/marketing', n: 1, text: 'Start marketing for x' }])
    expect(todoRows(zero, [m('x'), m('y')])[0]).toMatchObject({ href: '/studio/listings?tab=live', n: 2 })
    expect(todoRows({ ...zero, seo: 3 })[0].n).toBe(1)
    expect(todoRows(zero)).toEqual([])
  })

  it('setupSteps leaves the RERA step out for the owner', () => {
    const s = { hasLogo: true, hasRera: false, listings: 0, shared: false }
    expect(setupSteps({ ...s, owner: false }).map((x) => x.key)).toEqual(['brand', 'rera', 'listing', 'share'])
    expect(setupSteps({ ...s, owner: true }).map((x) => x.key)).toEqual(['brand', 'listing', 'share'])
  })
})

describe('demo data', () => {
  it('a logged call takes the person off the overdue list, like the server', async () => {
    const api = createFixtureApi({ getItem: () => null, setItem: () => undefined })
    await api.updateLead('c2', { call: 'answered' })
    expect((await api.getToday()).follow_ups.find((f) => f.id === 'c2')).toBeUndefined()
    await api.updateLead('c1', { call: 'no_answer' })
    expect((await api.getLead('c1')).stage).toBe('contacted')
  })
})
