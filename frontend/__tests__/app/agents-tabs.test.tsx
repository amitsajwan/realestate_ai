import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { AgentsScreen } from '@/components/app/agents/AgentsScreen'
import { fixtureAgents } from '@/lib/app/concierge'

const mockAdmin: Record<string, jest.Mock> = {}
;['inviteRequests', 'invite', 'dismiss'].forEach((n) => (mockAdmin[n] = jest.fn()))
const mockList = jest.fn()

jest.mock('next/navigation', () => ({ usePathname: () => '/studio/agents' }))
jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok', useSession: () => ({ ready: true, token: 't' }) }))
jest.mock('@/lib/app/client', () => ({ errorMessage: (e: Error) => e.message, isFixtureMode: () => false }))
jest.mock('@/lib/app/admin', () => ({
  ...jest.requireActual('@/lib/app/admin'),
  adminApi: new Proxy({}, { get: (_t, k: string) => (...a: unknown[]) => mockAdmin[k](...a) }),
}))
jest.mock('@/lib/app/concierge', () => ({
  ...jest.requireActual('@/lib/app/concierge'),
  conciergeApi: { list: (...a: unknown[]) => mockList(...a), create: jest.fn() },
}))
jest.mock('@/lib/app/share', () => ({ copyText: jest.fn(async () => true) }))
jest.mock('@/lib/app/whatsapp', () => ({
  getNotifications: jest.fn(async () => ({ unread: 2, items: [{ id: 'n1', kind: 'invite_request' }, { id: 'n2', kind: 'new_chat_lead' }] })),
  markNotificationRead: jest.fn(async () => undefined),
}))

// Rahul (7 of 8) and Sandeep (0 of 8) are setting up; Priya has finished.
const AGENTS = fixtureAgents().map(({ listings: _l, consent: _c, ...a }) =>
  a.id === 'fx-a2' ? { ...a, checklist: a.checklist.map((c) => ({ ...c, done: true })), progress: { done: 8, total: 8 } } : a)
const REQUESTS = () => jest.requireActual('@/lib/app/admin').fixtureOverview().invite_requests

beforeEach(() => {
  Object.values(mockAdmin).forEach((m) => m.mockReset())
  mockList.mockReset()
  mockList.mockResolvedValue(AGENTS)
  mockAdmin.inviteRequests.mockResolvedValue(REQUESTS())
  window.history.replaceState(null, '', '/studio/agents')
})

const tab = (name: RegExp) => screen.getByRole('tab', { name })

describe('Agents tabs', () => {
  it('splits agents into Setting up and Active, with counts, and opens on Setting up', async () => {
    render(<AgentsScreen />)
    await screen.findAllByTestId('agent-row')
    expect(tab(/Setting up/)).toHaveAttribute('aria-selected', 'true')
    expect(tab(/Setting up/)).toHaveTextContent('2')
    expect(tab(/Active/)).toHaveTextContent('1')
    expect(tab(/^All/)).toHaveTextContent('3')
    expect(screen.getAllByTestId('agent-row').map((r) => within(r).getByText(/Sharma|Patil|Kulkarni/).textContent)).toEqual(['Rahul Sharma', 'Sandeep Patil'])
    fireEvent.click(tab(/Active/))
    const rows = screen.getAllByTestId('agent-row')
    expect(rows).toHaveLength(1)
    expect(within(rows[0]).getByText('Active')).toBeInTheDocument()
    expect(window.location.search).toBe('?tab=active')
  })

  it('Asked to join has the website requests with a gold count; Invite shows the code once', async () => {
    mockAdmin.invite.mockResolvedValue({
      agent: { ...AGENTS[2], name: 'Vikram Joshi' }, created: true, code: '123456', reissued: false,
      whatsapp_message: 'Hi Vikram, welcome to Avasetu! Open https://x/join and your personal code 123456.', whatsapp_url: 'https://wa.me/919876500021',
      request: { ...REQUESTS()[0], status: 'invited' },
    })
    render(<AgentsScreen />)
    await screen.findAllByTestId('agent-row')
    const asked = tab(/Asked to join/)
    await waitFor(() => expect(asked).toHaveTextContent('2'))
    expect(asked.querySelector('span')!.className).toMatch(/f0b440/)
    fireEvent.click(asked)
    const rows = screen.getAllByTestId('invite-row')
    expect(rows).toHaveLength(2)
    expect(within(rows[0]).getByText(/98\*{6}21/)).toBeInTheDocument()
    fireEvent.click(within(rows[0]).getByRole('button', { name: 'Invite' }))
    expect(await screen.findByTestId('invite-code')).toHaveTextContent('123456')
    expect(mockAdmin.invite).toHaveBeenCalledWith('fx-r1')
    expect(mockAdmin.inviteRequests).toHaveBeenCalledTimes(2) // refreshed after the invite
    expect(mockList).toHaveBeenCalledTimes(2)
  })

  it('opening Asked to join clears only the "request to join" alerts; Dismiss asks first', async () => {
    const { markNotificationRead } = jest.requireMock('@/lib/app/whatsapp') as { markNotificationRead: jest.Mock }
    markNotificationRead.mockClear()
    mockAdmin.dismiss.mockResolvedValue({ status: 'dismissed' })
    window.history.replaceState(null, '', '/studio/agents?tab=asked')
    render(<AgentsScreen />)
    const row = (await screen.findAllByTestId('invite-row'))[1]
    await waitFor(() => expect(markNotificationRead).toHaveBeenCalledWith('n1'))
    expect(markNotificationRead).not.toHaveBeenCalledWith('n2')
    fireEvent.click(within(row).getByRole('button', { name: 'Dismiss' }))
    fireEvent.click(within(row).getByRole('button', { name: 'Keep' }))
    expect(mockAdmin.dismiss).not.toHaveBeenCalled()
    fireEvent.click(within(row).getByRole('button', { name: 'Dismiss' }))
    fireEvent.click(within(row).getByRole('button', { name: 'Yes, dismiss' }))
    await waitFor(() => expect(mockAdmin.dismiss).toHaveBeenCalledWith('fx-r2'))
  })

  it('says so when nobody asked to join', async () => {
    mockAdmin.inviteRequests.mockResolvedValue([])
    window.history.replaceState(null, '', '/studio/agents?tab=asked')
    render(<AgentsScreen />)
    expect(await screen.findByText('Nobody is waiting to join.')).toBeInTheDocument()
  })
})
