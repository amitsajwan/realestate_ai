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

describe('Interest tab: WhatsApp chats', () => {
  it('shows WhatsApp chats with the label, summary and last messages, and clears the badge', async () => {
    getWhatsAppConversations.mockResolvedValue([conv(), conv({ id: 'x2', name: null, needs_human: true })])
    getNotifications.mockResolvedValue({ items: [{ id: 'n1', kind: 'new_whatsapp_lead', summary: '', ref: {}, created_at: '', read: false }], unread: 1 })
    render(<InterestPage />)
    expect(await screen.findByText('Priya Sharma')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'WhatsApp chats' })).toBeInTheDocument()
    expect(screen.getAllByText('WhatsApp')).toHaveLength(2)
    expect(screen.getAllByText('WhatsApp enquiry (buy), area Kharadi, 2 BHK.')).toHaveLength(2)
    expect(screen.getAllByText('The price is ₹85 Lakh.')).toHaveLength(2)
    expect(screen.getAllByText('(Test mode, not sent)')).toHaveLength(2)
    expect(screen.getByText('1 need you')).toBeInTheDocument()
    expect(screen.getByText('WhatsApp buyer')).toBeInTheDocument()
    await waitFor(() => expect(markNotificationRead).toHaveBeenCalledWith('n1'))
  })

  it('warns when the buyer replied STOP', async () => {
    getWhatsAppConversations.mockResolvedValue([conv({ opted_out: true })])
    render(<InterestPage />)
    expect(await screen.findByText(/replied STOP/)).toBeInTheDocument()
  })

  it('shows no WhatsApp section when there are none or the call fails', async () => {
    getWhatsAppConversations.mockRejectedValue(new Error('down'))
    render(<InterestPage />)
    expect(await screen.findByText(/No comments yet/)).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'WhatsApp chats' })).not.toBeInTheDocument()
    expect(markNotificationRead).not.toHaveBeenCalled()
  })
})

describe('Studio home WhatsApp badge', () => {
  it('shows the count of unread WhatsApp notifications and links to the Interest tab', async () => {
    getNotifications.mockResolvedValue({
      items: [
        { id: 'n1', kind: 'new_whatsapp_lead', summary: '', ref: {}, created_at: '', read: false },
        { id: 'n2', kind: 'whatsapp_needs_you', summary: '', ref: {}, created_at: '', read: false },
      ],
      unread: 2,
    })
    render(<StudioHome />)
    const link = await screen.findByRole('link', { name: /new whatsapp leads and chats/i })
    expect(link).toHaveAttribute('href', '/studio/interest')
    expect(screen.getByLabelText('2 new')).toHaveTextContent('2')
    expect(getNotifications).toHaveBeenCalledWith(true)
  })

  it('shows nothing when there is nothing new', async () => {
    render(<StudioHome />)
    await waitFor(() => expect(getNotifications).toHaveBeenCalled())
    expect(screen.queryByText(/whatsapp/i)).not.toBeInTheDocument()
  })
})
