import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import AdminPage from '@/app/studio/admin/page'
import { ApiError } from '@/lib/app/api'
import { createAdminApi, createFixtureAdminApi, fixtureOverview, setupHints } from '@/lib/app/admin'
import type { AdminOverview } from '@/lib/app/admin'
import { fixtureAgents } from '@/lib/app/concierge'

const mockAdmin: Record<string, jest.Mock> = {}
;['overview', 'setControls', 'inviteRequests', 'invite', 'dismiss'].forEach((n) => (mockAdmin[n] = jest.fn()))
const mockCreate = jest.fn()

jest.mock('next/navigation', () => ({ usePathname: () => '/studio/admin' }))
jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok', useSession: () => ({ ready: true, token: 't' }) }))
jest.mock('@/lib/app/client', () => ({ errorMessage: (e: Error) => e.message, isFixtureMode: () => false }))
jest.mock('@/lib/app/admin', () => ({
  ...jest.requireActual('@/lib/app/admin'),
  adminApi: new Proxy({}, { get: (_t, k: string) => (...a: unknown[]) => mockAdmin[k](...a) }),
}))
jest.mock('@/lib/app/concierge', () => ({
  ...jest.requireActual('@/lib/app/concierge'),
  conciergeApi: { create: (...a: unknown[]) => mockCreate(...a) },
}))
jest.mock('@/lib/app/share', () => ({ copyText: jest.fn(async () => true) }))
jest.mock('@/lib/app/whatsapp', () => ({
  getNotifications: jest.fn(async () => ({ unread: 2, items: [{ id: 'n1', kind: 'invite_request' }, { id: 'n2', kind: 'new_chat_lead' }] })),
  markNotificationRead: jest.fn(async () => undefined),
}))

const AGENTS = fixtureAgents().map(({ listings: _l, consent: _c, ...s }) => s)
const overview = (over: Partial<AdminOverview> = {}): AdminOverview => ({ ...fixtureOverview(), agents: AGENTS, ...over })

beforeEach(() => {
  Object.values(mockAdmin).forEach((m) => m.mockReset())
  mockCreate.mockReset()
  mockAdmin.overview.mockResolvedValue(overview())
})

describe('Admin home', () => {
  it('no longer clears the "new request to join" alerts (the requests live under Agents now)', async () => {
    const { getNotifications } = jest.requireMock('@/lib/app/whatsapp') as { getNotifications: jest.Mock }
    getNotifications.mockClear()
    render(<AdminPage />)
    await screen.findByTestId('admin-screen')
    expect(getNotifications).not.toHaveBeenCalled()
  })
  it('shows the sections in order: Add agent, Today, Needs you, Agents, Health, Controls', async () => {
    render(<AdminPage />)
    await screen.findByTestId('admin-screen')
    const ids = Array.from(document.querySelectorAll('[data-testid^=admin-]')).map((e) => e.getAttribute('data-testid'))
    expect(ids.filter((x) => ['admin-add-agent', 'admin-today', 'admin-needs', 'admin-agents', 'admin-health', 'admin-controls'].includes(x as string)))
      .toEqual(['admin-add-agent', 'admin-today', 'admin-needs', 'admin-agents', 'admin-health', 'admin-controls'])
  })

  it('count tiles show today and the week, and link to the right screens', async () => {
    render(<AdminPage />)
    const leads = await screen.findByTestId('tile-leads')
    expect(leads).toHaveAttribute('href', '/studio/leads')
    expect(within(leads).getByText('3')).toBeInTheDocument()
    expect(within(leads).getByText(/15 in 7 days/)).toBeInTheDocument()
    expect(screen.getByTestId('tile-interest')).toHaveAttribute('href', '/studio/interest')
    expect(screen.getByTestId('tile-posts')).toHaveAttribute('href', '/studio/content')
    expect(within(screen.getByTestId('tile-posts')).getByText('2')).toBeInTheDocument()
    expect(screen.getByTestId('tile-news')).toHaveAttribute('href', '/studio/newsroom')
  })

  it('Needs you lists approvals and links the website requests to Agents > Asked to join', async () => {
    render(<AdminPage />)
    expect(await screen.findByTestId('needs-posts')).toHaveAttribute('href', '/studio/content')
    expect(screen.getByTestId('needs-posts')).toHaveTextContent('4 posts wait for your approval')
    expect(screen.getByTestId('needs-news')).toHaveTextContent('2 news stories to review')
    const asked = screen.getByTestId('needs-asked')
    expect(asked).toHaveTextContent('2 asked to join on the website')
    expect(asked).toHaveAttribute('href', '/studio/agents?tab=asked')
    expect(screen.queryByTestId('invite-row')).toBeNull()
  })

  it('shows a calm empty state when nothing waits', async () => {
    mockAdmin.overview.mockResolvedValue(overview({ waiting: { posts: 0, news: 0, invite_requests: 0 }, invite_requests: [] }))
    render(<AdminPage />)
    expect(await screen.findByText('Nothing is waiting for you right now.')).toBeInTheDocument()
  })

  it('agents have a progress ring, a masked mobile, finish-setup hints and open the detail screen', async () => {
    render(<AdminPage />)
    const rows = await screen.findAllByTestId('admin-agent-row')
    expect(rows).toHaveLength(3)
    expect(rows[1]).toHaveAttribute('href', '/studio/agents/fx-a2')
    expect(within(rows[1]).getByRole('img', { name: '2 of 8 steps done' })).toBeInTheDocument()
    expect(within(rows[1]).getByText(/99\*{6}42/)).toBeInTheDocument()
    expect(within(rows[1]).getByText('Finish setup: add logo, add banner, add RERA number')).toBeInTheDocument()
    expect(within(rows[0]).getByText(/reach 3 listings/)).toBeInTheDocument()
  })

  it('health rows are green, amber or red with the fix text', async () => {
    render(<AdminPage />)
    const rows = await screen.findAllByTestId('health-row')
    expect(rows.map((r) => r.textContent?.split(' ')[0])).toEqual(['Facebook', 'Instagram', 'WhatsApp', 'AI', 'Posting', 'Comments', 'News'])
    const ig = rows[1]
    expect(ig).toHaveAttribute('data-status', 'bad')
    expect(ig).toHaveTextContent('Fix: Run deploy/gcp/meta_connect.ps1')
    expect(rows[0]).toHaveAttribute('data-status', 'ok')
    expect(rows[0]).not.toHaveTextContent('Fix:')
  })

  it('pause switches ask for confirmation before changing anything', async () => {
    mockAdmin.setControls.mockResolvedValue({ ...fixtureOverview().controls, posting_paused: true, updated_at: '2026-10-02T06:00:00Z' })
    render(<AdminPage />)
    const sw = await screen.findByRole('switch', { name: 'Pause posting' })
    expect(sw).toHaveAttribute('aria-checked', 'false')
    fireEvent.click(sw)
    expect(screen.getByTestId('control-confirm')).toHaveTextContent('Scheduled Facebook and Instagram posts stop')
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(mockAdmin.setControls).not.toHaveBeenCalled()
    fireEvent.click(sw)
    mockAdmin.overview.mockResolvedValue(overview({ controls: { ...fixtureOverview().controls, posting_paused: true } }))
    fireEvent.click(screen.getByRole('button', { name: 'Yes, pause posting' }))
    await waitFor(() => expect(mockAdmin.setControls).toHaveBeenCalledWith({ posting_paused: true }))
    await waitFor(() => expect(screen.getByRole('switch', { name: 'Pause posting' })).toHaveAttribute('aria-checked', 'true'))
  })

  it('a paused switch offers to resume', async () => {
    mockAdmin.overview.mockResolvedValue(overview({ controls: { ...fixtureOverview().controls, news_paused: true } }))
    render(<AdminPage />)
    fireEvent.click(await screen.findByRole('switch', { name: 'Pause news' }))
    expect(screen.getByRole('button', { name: 'Yes, resume news' })).toBeInTheDocument()
  })

  it('Add agent opens the existing sheet', async () => {
    render(<AdminPage />)
    fireEvent.click(await screen.findByTestId('admin-add-agent'))
    expect(screen.getByRole('dialog', { name: 'Add agent' })).toBeInTheDocument()
    expect(screen.getByLabelText('His mobile number')).toBeInTheDocument()
  })

  it('shows the server message to anyone who is not the owner', async () => {
    mockAdmin.overview.mockRejectedValue(new Error('Only the Avasetu owner can open Admin'))
    render(<AdminPage />)
    expect(await screen.findByText('Only the Avasetu owner can open Admin')).toBeInTheDocument()
  })
})

describe('admin client and fixtures', () => {
  it('calls the /admin endpoints with the token', async () => {
    const calls: Array<[string, RequestInit]> = []
    const fetchImpl = jest.fn(async (url: string, init: RequestInit) => {
      calls.push([url, init])
      return { ok: true, status: 200, text: async () => (url.endsWith('/invite-requests') ? '{"items":[]}' : '{}') } as Response
    }) as unknown as typeof fetch
    const api = createAdminApi({ getToken: () => 'T', baseUrl: 'https://b', fetchImpl })
    await api.overview()
    await api.setControls({ comments_paused: true })
    await api.inviteRequests()
    await api.invite('r 1')
    await api.dismiss('r1')
    expect(calls.map(([u, i]) => `${i.method} ${u}`)).toEqual([
      'GET https://b/api/v1/admin/overview', 'POST https://b/api/v1/admin/controls', 'GET https://b/api/v1/admin/invite-requests',
      'POST https://b/api/v1/admin/invite-requests/r%201/invite', 'POST https://b/api/v1/admin/invite-requests/r1/dismiss',
    ])
    expect(calls[1][1].body).toBe('{"comments_paused":true}')
    expect((calls[0][1].headers as Record<string, string>).Authorization).toBe('Bearer T')
  })

  it('unwraps server errors', async () => {
    const fetchImpl = (async () => ({ ok: false, status: 403, text: async () => '{"error":{"message":"Only the Avasetu owner can open Admin"}}' })) as unknown as typeof fetch
    await expect(createAdminApi({ getToken: () => null, baseUrl: 'https://b', fetchImpl }).overview()).rejects.toThrow(ApiError)
  })

  it('fixture invite removes the request and adds the agent; pausing marks health', async () => {
    const api = createFixtureAdminApi()
    const before = await api.overview()
    const r = await api.invite(before.invite_requests[0].id)
    expect(r.code).toHaveLength(6)
    const after = await api.overview()
    expect(after.invite_requests).toHaveLength(1)
    expect(after.agents[0].name).toBe('Vikram Joshi')
    await api.setControls({ posting_paused: true })
    const o = await api.overview()
    expect(o.controls.posting_paused).toBe(true)
    expect(o.health.find((h) => h.key === 'posting')?.text).toBe('Paused by you')
    await expect(api.dismiss('nope')).rejects.toThrow('Invite request not found')
  })

  it('setupHints turns the checklist into short plain hints', () => {
    expect(setupHints(fixtureAgents()[2], 2)).toEqual(['add logo', 'add banner'])
    expect(setupHints({ checklist: [] })).toEqual([])
  })
})
