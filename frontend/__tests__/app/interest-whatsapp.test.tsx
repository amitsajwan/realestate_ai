import { render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import InterestPage from '@/app/studio/interest/page'
import StudioHome from '@/app/studio/page'
import type { WhatsAppConversation } from '@/lib/app/whatsapp'

jest.mock('@/lib/app/client', () => ({
  api: {
    getFacebookInterest: async () => [],
    getChatConversations: async () => [],
    getFacebookStatus: async () => ({ ok: true, reconnect: false, checked_at: null }),
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))
const getWhatsAppConversations = jest.fn()
const getNotifications = jest.fn()
const markNotificationRead = jest.fn()
jest.mock('@/lib/app/whatsapp', () => ({
  ...jest.requireActual('@/lib/app/whatsapp'),
  getWhatsAppConversations: () => getWhatsAppConversations(),
  getNotifications: (u: boolean) => getNotifications(u),
  markNotificationRead: (id: string) => markNotificationRead(id),
}))
jest.mock('@/components/app/BusinessToday', () => ({ BusinessToday: () => <div>today</div> }))
jest.mock('@/components/app/WeeklyCard', () => ({ WeeklyCard: () => <div>weekly</div> }))

const conv = (over: Partial<WhatsAppConversation> = {}): WhatsAppConversation => ({
  id: '3210-abcd', channel: 'whatsapp', name: 'Priya Sharma', phone: '+91 98******10', lead_id: 'C1',
  summary: 'WhatsApp enquiry (buy), area Kharadi, 2 BHK.', needs_human: false, opted_out: false, updated_at: null, language: 'en',
  interest_title: '2 BHK in Kharadi', window_open: true,
  messages: [
    { role: 'user', text: 'Hi, I am interested in 2 BHK in Kharadi (ref abcd234)', ts: '2026-10-01T10:00:00' },
    { role: 'bot', text: 'The price is ₹85 Lakh.', ts: '2026-10-01T10:00:00', status: 'dry_run' },
  ],
  ...over,
})

beforeEach(() => {
  getWhatsAppConversations.mockReset()
  getNotifications.mockReset().mockResolvedValue({ items: [], unread: 0 })
  markNotificationRead.mockReset().mockResolvedValue(undefined)
})

describe('Interest tab', () => {
  it('sends people to the Inbox for chats instead of listing them', async () => {
    render(<InterestPage />)
    const link = await screen.findByRole('link', { name: /chats are in inbox/i })
    expect(link).toHaveAttribute('href', '/studio/inbox')
    expect(getWhatsAppConversations).not.toHaveBeenCalled()
  })
})

describe('Studio home WhatsApp badge', () => {
  it('shows the count of unread WhatsApp notifications and links to the Inbox', async () => {
    getNotifications.mockResolvedValue({
      items: [
        { id: 'n1', kind: 'new_whatsapp_lead', summary: '', ref: {}, created_at: '', read: false },
        { id: 'n2', kind: 'whatsapp_needs_you', summary: '', ref: {}, created_at: '', read: false },
      ],
      unread: 2,
    })
    render(<StudioHome />)
    const link = await screen.findByRole('link', { name: /new whatsapp leads and chats/i })
    expect(link).toHaveAttribute('href', '/studio/inbox')
    expect(screen.getByLabelText('2 new')).toHaveTextContent('2')
    expect(getNotifications).toHaveBeenCalledWith(true)
  })

  it('shows nothing when there is nothing new', async () => {
    render(<StudioHome />)
    await waitFor(() => expect(getNotifications).toHaveBeenCalled())
    expect(screen.queryByText(/whatsapp/i)).not.toBeInTheDocument()
  })
})
