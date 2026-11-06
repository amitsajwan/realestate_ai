import React from 'react'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ChatWidget, { ChatHomeCard } from '@/components/site/ChatWidget'
import { cardFacts, parseChatReply } from '@/lib/site/chatApi'
import { askNow, isMuted, nudgeAllowed, parseNudge } from '@/lib/site/chatNudge'

const mockTrackEvent = jest.fn()
jest.mock('@/lib/site/tracking', () => ({
  readAttribution: () => ({ source: 'chat' }), getAnonId: () => 'anon12345', readVisitPages: () => ({ path: '/agent/rahul', landing: '/agent/rahul' }),
  trackEvent: (...args: unknown[]) => mockTrackEvent(...args),
}))

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
    // the visitor's story says they opened the chat: once for the page, not once per message
    expect(mockTrackEvent.mock.calls).toEqual([['chat_open', 'rahul']])
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

describe('the note beside the chat button', () => {
  const NOTE = { text: 'Comparing A and B?', quick_replies: ['Compare them'], link: { label: 'Try the home plan', url: '/home-plan' } }

  /** The widget's clock, run up to the first moment it asks the server. */
  async function until(asked: jest.Mock) {
    for (let i = 0; i < 6 && !asked.mock.calls.length; i++) await act(async () => { jest.advanceTimersByTime(5000) })
  }

  beforeEach(() => {
    window.sessionStorage.clear()
    jest.useFakeTimers()
    window.history.pushState({}, '', '/projects/lodha-camelot')
  })
  afterEach(() => { jest.useRealTimers() })

  function server(note: object | null) {
    const asked = jest.fn((url: string) => reply(url.endsWith('/nudge') ? note as object : { reply: 'Sure', quick_replies: [] }))
    global.fetch = asked as unknown as typeof fetch
    return asked
  }

  it('asks after a while in view, shows beside the button and never opens the chat', async () => {
    const asked = server(NOTE)
    render(<ChatWidget agentSlug="avasetu" />)
    await until(asked)
    await act(async () => { await Promise.resolve() })
    expect(screen.getByTestId('chat-nudge')).toHaveTextContent('Comparing A and B?')
    expect(screen.queryByRole('log')).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Try the home plan' })).toHaveAttribute('href', '/home-plan')
  })

  it('becomes the first message of the chat when they tap it, and their tap is sent', async () => {
    const asked = server(NOTE)
    render(<ChatWidget agentSlug="avasetu" />)
    await until(asked)
    await act(async () => { await Promise.resolve() })
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Compare them' })) })
    expect(within(screen.getByRole('log')).getByText('Comparing A and B?')).toBeInTheDocument()
    expect(within(screen.getByRole('log')).getByText('Compare them')).toBeInTheDocument()
    expect(asked.mock.calls.some((c) => String(c[0]).endsWith('/chat/message'))).toBe(true)
  })

  it('stays away for a week once dismissed', async () => {
    const asked = server(NOTE)
    render(<ChatWidget agentSlug="avasetu" />)
    await until(asked)
    await act(async () => { await Promise.resolve() })
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss message' }))
    expect(screen.queryByTestId('chat-nudge')).not.toBeInTheDocument()
    expect(isMuted(Date.now())).toBe(true)
    expect(isMuted(Date.now() + 8 * 24 * 60 * 60 * 1000)).toBe(false)
  })

  it('never interrupts a form, a sign-in or an agent page; a finished plan is fine', () => {
    expect(nudgeAllowed('/projects/lodha-camelot')).toBe(true)
    expect(nudgeAllowed('/home-plan/result')).toBe(true)
    for (const p of ['/home-plan', '/enquire', '/login', '/agents', '/agent/rahul', '/for-agents/guide']) expect(nudgeAllowed(p)).toBe(false)
  })

  it('keeps asking each minute for a while, for a plan made late in a long visit', () => {
    expect([25, 30, 90, 120, 180, 185, 240, 1200, 1260].filter(askNow)).toEqual([30, 90, 120, 180, 240, 1200])
  })

  it('reads a note defensively', () => {
    expect(parseNudge(null)).toBeNull()
    expect(parseNudge({ text: '' })).toBeNull()
    expect(parseNudge({ text: 'x', link: { label: 'y', url: 'javascript:alert(1)' } })).toEqual({ text: 'x', quick_replies: [], link: null })
  })
})

describe('the chat header', () => {
  it('offers Hindi and Marathi at any time', async () => {
    const asked = jest.fn(() => reply({ reply: 'नमस्कार', quick_replies: [] }))
    global.fetch = asked as unknown as typeof fetch
    render(<ChatWidget agentSlug="avasetu" />)
    await act(async () => { fireEvent.click(screen.getByTestId('chat-open')) })
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'मराठी' })) })
    const calls = asked.mock.calls as unknown[][]
    expect(JSON.parse(String((calls[calls.length - 1][1] as RequestInit).body)).message).toBe('मराठी')
  })
})

describe('project cards and the plan link', () => {
  it('shows the fact and a Hot mark', () => {
    render(<ul><ChatHomeCard card={{ ...REAL, hot: true, fact: '12 homes booked lately' }} /></ul>)
    expect(screen.getByRole('link')).toHaveTextContent('Hot')
    expect(screen.getByRole('link')).toHaveTextContent('12 homes booked lately')
  })
  it('keeps a safe link and drops another', () => {
    expect(parseChatReply({ reply: 'x', link: { label: 'Try', url: '/home-plan?bhk=2' } }).link).toEqual({ label: 'Try', url: '/home-plan?bhk=2' })
    expect(parseChatReply({ reply: 'x', link: { label: 'Try', url: 'javascript:alert(1)' } }).link).toBeUndefined()
  })
})
