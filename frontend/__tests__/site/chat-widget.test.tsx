import React from 'react'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ChatWidget, { ChatHomeCard } from '@/components/site/ChatWidget'
import { cardFacts, parseChatReply } from '@/lib/site/chatApi'
import { LeadAlertsBadge, alertsLabel } from '@/components/app/LeadAlertsBadge'

jest.mock('@/lib/site/tracking', () => ({ readAttribution: () => ({ source: 'chat' }) }))
jest.mock('@/lib/app/whatsapp', () => ({ getNotifications: jest.fn() }))

const REAL = { id: 'L2', title: '2 BHK in Kharadi, east facing', locality: 'Kharadi', bhk: 2, carpet_sqft: 810, price_text: '₹76 Lakh', sample: false,
  url: '/agent/rahul/listings/L2', image_url: 'https://img.test/L2.jpg' }
const SAMPLE = { ...REAL, id: 'L3', title: '2 BHK near EON IT Park', carpet_sqft: 760, price_text: null, sample: true, url: '/agent/demo/listings/L3', image_url: null }

function reply(body: object) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response)
}

beforeEach(() => {
  window.localStorage.clear()
})

describe('chat reply parsing', () => {
  it('keeps at most three safe cards and never a price on a sample', () => {
    const r = parseChatReply({ reply: 'Here', quick_replies: ['Buy'], cards: [REAL, { ...SAMPLE, price_text: '₹82 Lakh' }, { ...REAL, id: 'X', url: 'javascript:alert(1)' }, REAL, REAL] })
    expect(r.cards.map((c) => c.id)).toEqual(['L2', 'L3', 'L2'])
    expect(r.cards[1].price_text).toBeNull()
    expect(cardFacts(r.cards[0])).toBe('Kharadi · 2 BHK · 810 sq ft')
  })
  it('drops "Continue on WhatsApp" without a wa.me link, and any other link', () => {
    expect(parseChatReply({ reply: 'x', quick_replies: ['Yes', 'Continue on WhatsApp'] }).quick_replies).toEqual(['Yes'])
    expect(parseChatReply({ reply: 'x', quick_replies: ['Continue on WhatsApp'], whatsapp_url: 'https://evil.test/x' }).whatsapp_url).toBeNull()
    const ok = parseChatReply({ reply: 'x', quick_replies: ['Continue on WhatsApp'], whatsapp_url: 'https://wa.me/919876543210?text=hi' })
    expect(ok.quick_replies).toEqual(['Continue on WhatsApp'])
  })
  it('reads an older server reply without cards', () => {
    expect(parseChatReply({ reply: 'Hi', quick_replies: [] })).toEqual({ reply: 'Hi', quick_replies: [], lead_created: false, cards: [], follow_up: null, whatsapp_url: null })
  })
})

describe('ChatHomeCard', () => {
  it('shows image, title, area facts and the price, linking to the listing', () => {
    render(<ul><ChatHomeCard card={REAL} /></ul>)
    const a = screen.getByRole('link')
    expect(a).toHaveAttribute('href', '/agent/rahul/listings/L2')
    expect(a).toHaveTextContent('2 BHK in Kharadi, east facing')
    expect(a).toHaveTextContent('Kharadi · 2 BHK · 810 sq ft')
    expect(a).toHaveTextContent('₹76 Lakh')
    expect(a.querySelector('img')).toHaveAttribute('src', 'https://img.test/L2.jpg')
    expect(a).not.toHaveTextContent('Sample')
  })
  it('labels a sample and shows no price', () => {
    render(<ul><ChatHomeCard card={SAMPLE} /></ul>)
    const a = screen.getByRole('link')
    expect(within(a).getByText('Sample')).toBeInTheDocument()
    expect(a).not.toHaveTextContent('₹')
  })
})

describe('ChatWidget', () => {
  it('renders home cards and quick replies from the reply, and WhatsApp as a link only with a URL', async () => {
    const fetchMock = jest.fn()
      .mockImplementationOnce(() => reply({ reply: 'Asking about the 2 BHK in Kharadi, 780 sq ft?', quick_replies: ['Tell me about it', 'Similar homes', 'Continue on WhatsApp'],
        whatsapp_url: 'https://wa.me/919876543210?text=Hi%20(ref%20abcd234)' }))
      .mockImplementationOnce(() => reply({ reply: 'Here are 2 homes that fit what you told me. Homes marked Sample are illustrations, not for sale.',
        quick_replies: ['Not now'], cards: [REAL, SAMPLE], follow_up: 'When are you planning to move?' }))
    global.fetch = fetchMock as unknown as typeof fetch
    render(<ChatWidget agentSlug="rahul" />)
    fireEvent.click(screen.getByRole('button', { name: /chat with us/i }))
    await screen.findByText(/Asking about the 2 BHK/)
    const wa = screen.getByRole('link', { name: 'Continue on WhatsApp' })
    expect(wa).toHaveAttribute('href', 'https://wa.me/919876543210?text=Hi%20(ref%20abcd234)')
    expect(wa).toHaveAttribute('target', '_blank')
    fireEvent.click(screen.getByRole('button', { name: 'Similar homes' }))
    const list = await screen.findByRole('list', { name: 'Matching homes' })
    const cards = within(list).getAllByTestId('chat-home-card')
    expect(cards).toHaveLength(2)
    expect(cards[1]).toHaveTextContent('Sample')
    // the next question is its own bubble after the cards
    const followUp = screen.getByText('When are you planning to move?')
    expect(list.compareDocumentPosition(followUp) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Not now' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Continue on WhatsApp' })).toBeNull()
    const body = JSON.parse(fetchMock.mock.calls[1][1].body)
    expect(body).toMatchObject({ agent_slug: 'rahul', message: 'Similar homes' })
  })
})

describe('ChatWidget bubble', () => {
  it('is a small round icon button on phones, named "Chat with us", with the words only from 640 px up', () => {
    render(<ChatWidget agentSlug="rahul" />)
    const btn = screen.getByRole('button', { name: 'Chat with us' })
    expect(btn.className).toMatch(/\bh-12\b/)
    expect(btn.className).toMatch(/\bw-12\b/)
    expect(btn.className).toMatch(/\brounded-full\b/)
    expect(within(btn).getByText('Chat with us').className).toMatch(/\bhidden sm:inline\b/)
  })

  it('sits above the agent site bar by default, in the corner without one, clear of the phone home bar', () => {
    const { unmount } = render(<ChatWidget agentSlug="rahul" />)
    expect(screen.getByTestId('chat-widget').className).toContain('bottom-[calc(5rem+env(safe-area-inset-bottom,0px))]')
    unmount()
    render(<ChatWidget agentSlug="rahul" bottomBar={false} />)
    expect(screen.getByTestId('chat-widget').className).toContain('bottom-[calc(1rem+env(safe-area-inset-bottom,0px))]')
  })
})

describe('LeadAlertsBadge', () => {
  const { getNotifications } = jest.requireMock('@/lib/app/whatsapp') as { getNotifications: jest.Mock }
  it('counts website chat alerts as well as WhatsApp ones', async () => {
    getNotifications.mockResolvedValue({ unread: 2, items: [{ id: '1', kind: 'new_chat_lead', summary: '', ref: {}, created_at: '', read: false },
      { id: '2', kind: 'new_whatsapp_lead', summary: '', ref: {}, created_at: '', read: false }] })
    render(<LeadAlertsBadge />)
    await waitFor(() => expect(screen.getByTestId('lead-alerts-badge')).toHaveTextContent('2New leads and chats'))
  })
  it('names the channel when all alerts come from one', () => {
    expect(alertsLabel([{ id: '1', kind: 'chat_needs_you', summary: '', ref: {}, created_at: '', read: false }], 1)).toBe('New lead or chat from your website')
  })
})
