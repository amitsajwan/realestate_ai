import { fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'
import InboxPage from '@/app/studio/inbox/page'
import InboxThreadPage from '@/app/studio/inbox/[id]/page'
import { QUICK_REPLIES } from '@/lib/app/inbox'

const threads = jest.fn()
const thread = jest.fn()
jest.mock('@/lib/app/inbox', () => ({
  ...jest.requireActual('@/lib/app/inbox'),
  inboxApi: { threads: () => threads(), thread: (id: string) => thread(id) },
}))
jest.mock('@/lib/app/whatsapp', () => ({ getNotifications: async () => ({ items: [], unread: 0 }), markNotificationRead: async () => undefined }))
jest.mock('next/navigation', () => ({ useParams: () => ({ id: 't1' }) }))

const row = (id: string, needs_you: boolean) => ({
  id, channel: 'whatsapp', name: id, phone: '', role: 'buyer', last_text: 'hi', last_from: 'them', last_at: null, needs_you,
  lead_id: null, lead_saved: false, window_open: true, opted_out: false, can_reply: true, summary: '', messages: 1, passed: null, passed_at: null,
})

beforeAll(() => { Element.prototype.scrollIntoView = jest.fn() })   // jsdom has none; the thread scrolls to its last message

beforeEach(() => {
  window.history.replaceState(null, '', '/studio/inbox')
  threads.mockReset()
  thread.mockReset()
})

describe('Inbox', () => {
  it('opens on Needs you while someone waits for an answer', async () => {
    threads.mockResolvedValue([row('a', true), row('b', false)])
    render(<InboxPage />)
    const tab = await screen.findByRole('tab', { name: /Needs you/ })
    expect(tab).toHaveAttribute('aria-selected', 'true')
    expect(screen.getAllByTestId('inbox-row')).toHaveLength(1)
  })

  it('opens on All when nobody waits', async () => {
    threads.mockResolvedValue([row('b', false)])
    render(<InboxPage />)
    expect(await screen.findByRole('tab', { name: /All/ })).toHaveAttribute('aria-selected', 'true')
  })

  it('a quick reply fills the reply box and is not sent by itself', async () => {
    thread.mockResolvedValue({ ...row('t1', true), thread: [], bot_paused_until: null, passed_to_name: null })
    render(<InboxThreadPage />)
    const box = await screen.findByRole('region', { name: 'Reply' })
    fireEvent.click(within(box).getByRole('button', { name: QUICK_REPLIES[1] }))
    expect(within(box).getByRole('textbox')).toHaveValue(QUICK_REPLIES[1])
  })
})
