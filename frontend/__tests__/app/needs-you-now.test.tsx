import { render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { NeedsYouNow } from '@/components/app/NeedsYouNow'

const getNotifications = jest.fn()
const threads = jest.fn()
const getToday = jest.fn()
const getUpcoming = jest.fn()
let mockOwner = false
jest.mock('@/lib/app/whatsapp', () => ({ getNotifications: (u: boolean) => getNotifications(u) }))
jest.mock('@/lib/app/inbox', () => ({ inboxApi: { threads: () => threads() } }))
jest.mock('@/lib/app/client', () => ({ api: { getToday: () => getToday() } }))
jest.mock('@/lib/app/content', () => ({ contentApi: { getUpcoming: () => getUpcoming() } }))
jest.mock('@/components/app/agents/useIsOwner', () => ({ useIsOwner: () => mockOwner }))
jest.mock('@/components/app/AppShell', () => ({ countWaitingPosts: (x: unknown[]) => x.length }))

const note = (kind: string) => ({ id: kind + Math.random(), kind, summary: '', ref: {}, created_at: '', read: false })

beforeEach(() => {
  mockOwner = false
  getNotifications.mockReset().mockResolvedValue({ items: [], unread: 0 })
  threads.mockReset().mockResolvedValue([])
  getToday.mockReset().mockResolvedValue({ follow_ups: [] })
  getUpcoming.mockReset().mockResolvedValue([])
})

describe('Needs you now', () => {
  it('lists what is waiting, each opening its list, and leaves out a source that fails', async () => {
    mockOwner = true
    threads.mockResolvedValue([{ needs_you: true }, { needs_you: true }, { needs_you: false }])
    getNotifications.mockResolvedValue({ items: [note('buyer_passed'), note('invite_request'), note('new_chat_lead')], unread: 3 })
    getToday.mockRejectedValue(new Error('down'))
    getUpcoming.mockResolvedValue([{}, {}, {}])
    render(<NeedsYouNow />)
    await waitFor(() => expect(screen.getByTestId('needs-inbox')).toHaveTextContent('2chats and comments waiting for an answer'))
    expect(screen.getByTestId('needs-inbox')).toHaveAttribute('href', '/studio/inbox?tab=needs')
    expect(screen.getByTestId('needs-passed')).toHaveTextContent('1buyer was passed to you')
    expect(screen.getByTestId('needs-posts')).toHaveAttribute('href', '/studio/content')
    expect(screen.getByTestId('needs-invites')).toHaveTextContent('1request to join')
    expect(screen.queryByTestId('needs-calls')).toBeNull()
  })

  it('says all caught up when nothing waits, and agents are never asked about posts', async () => {
    render(<NeedsYouNow />)
    await waitFor(() => expect(screen.getByText('All caught up')).toBeInTheDocument())
    expect(getUpcoming).not.toHaveBeenCalled()
  })
})
