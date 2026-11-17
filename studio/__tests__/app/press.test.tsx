import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import PressPage from '@/app/studio/press/page'
import { gmailComposeUrl, mailtoUrl } from '@/lib/app/press'
import type { PressPitch, PressStory, PressSummary } from '@/lib/app/press'

const mockPress: Record<string, jest.Mock> = {}
;['story', 'pitches', 'summary', 'patch', 'runNow'].forEach((n) => (mockPress[n] = jest.fn()))

jest.mock('next/navigation', () => ({ usePathname: () => '/studio/press' }))
jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok', useSession: () => ({ ready: true, token: 't' }) }))
jest.mock('@/lib/app/client', () => ({ errorMessage: (e: Error) => e.message, isFixtureMode: () => false }))
jest.mock('@/lib/app/press', () => ({
  ...jest.requireActual('@/lib/app/press'),
  pressApi: new Proxy({}, { get: (_t, k: string) => (...a: unknown[]) => mockPress[k](...a) }),
}))

const story: PressStory = {
  month: '2026-11',
  facts: [],
  headline_facts: [
    { text: 'Kharadi registered 4 new MahaRERA projects in October 2026.', area: 'kharadi', topic: 'registrations',
      source: 'MahaRERA public records, read by Avasetu', as_of: '2026-11-17' },
  ],
}
const summary: PressSummary = { sent: 2, replied: 1, links_won: 1 }

function pitch(over: Partial<PressPitch> = {}): PressPitch {
  return {
    id: 'p1', month: '2026-11', journalist: { name: 'Priya Sharma', outlet: 'Hindustan Times', email: 'priya@ht.example', contact_page: null },
    article: { title: "Kharadi's housing boom", url: 'https://hindustantimes.com/a', date: '2 days ago' },
    email: 'priya@ht.example', subject: 'Pune MahaRERA data for your story', body: 'Kharadi registered 4 new projects.',
    origin: 'template', status: 'draft', replied: false, link_won_url: null, ...over,
  }
}

beforeEach(() => {
  Object.values(mockPress).forEach((m) => m.mockReset())
  mockPress.story.mockResolvedValue(story)
  mockPress.summary.mockResolvedValue(summary)
  mockPress.pitches.mockResolvedValue([pitch()])
})

describe('Press', () => {
  it('shows this month\'s headline facts and the summary counts', async () => {
    render(<PressPage />)
    await screen.findByTestId('press-screen')
    expect(screen.getByText(/Kharadi registered 4 new MahaRERA projects/)).toBeInTheDocument()
    const summaryBox = screen.getByTestId('press-summary')
    expect(within(summaryBox).getByText('2')).toBeInTheDocument()
    expect(within(summaryBox).getAllByText('1')).toHaveLength(2)
  })

  it('shows a draft with the journalist, outlet and article link', async () => {
    render(<PressPage />)
    const card = await screen.findByTestId('press-pitch')
    expect(within(card).getByText(/Hindustan Times/)).toBeInTheDocument()
    expect(within(card).getByText(/Priya Sharma/)).toBeInTheDocument()
    const link = within(card).getByRole('link', { name: /housing boom/ })
    expect(link).toHaveAttribute('href', 'https://hindustantimes.com/a')
  })

  it('the Gmail link encodes the subject and body', async () => {
    render(<PressPage />)
    const card = await screen.findByTestId('press-pitch')
    const gmail = within(card).getByTestId('press-gmail') as HTMLAnchorElement
    const url = new URL(gmail.href)
    expect(url.hostname).toBe('mail.google.com')
    expect(url.searchParams.get('su')).toBe('Pune MahaRERA data for your story')
    expect(url.searchParams.get('body')).toBe('Kharadi registered 4 new projects.')
    expect(url.searchParams.get('to')).toBe('priya@ht.example')
  })

  it('a mailto link is also offered', async () => {
    render(<PressPage />)
    const card = await screen.findByTestId('press-pitch')
    const mailto = within(card).getByTestId('press-mailto') as HTMLAnchorElement
    expect(mailto.href.startsWith('mailto:priya@ht.example?')).toBe(true)
  })

  it('no email on file: "find the contact" is shown instead of a Gmail "to"', async () => {
    mockPress.pitches.mockResolvedValue([pitch({ email: null, journalist: { name: null, outlet: 'Hindustan Times', email: null, contact_page: 'https://hindustantimes.com/contact' } })])
    render(<PressPage />)
    const card = await screen.findByTestId('press-pitch')
    expect(within(card).getByText(/find the contact/i)).toBeInTheDocument()
    expect(within(card).getByRole('link', { name: /contact page/i })).toHaveAttribute('href', 'https://hindustantimes.com/contact')
    const gmail = within(card).getByTestId('press-gmail') as HTMLAnchorElement
    expect(new URL(gmail.href).searchParams.get('to')).toBe('')
  })

  it('Mark sent updates the status', async () => {
    mockPress.patch.mockResolvedValue(pitch({ status: 'sent' }))
    render(<PressPage />)
    const card = await screen.findByTestId('press-pitch')
    fireEvent.click(within(card).getByText('Mark sent'))
    await waitFor(() => expect(mockPress.patch).toHaveBeenCalledWith('p1', { status: 'sent' }))
    await waitFor(() => expect(within(card).getByTestId('press-status').textContent).toBe('Sent'))
  })

  it('Skip updates the status', async () => {
    mockPress.patch.mockResolvedValue(pitch({ status: 'skipped' }))
    render(<PressPage />)
    const card = await screen.findByTestId('press-pitch')
    fireEvent.click(within(card).getByText('Skip'))
    await waitFor(() => expect(mockPress.patch).toHaveBeenCalledWith('p1', { status: 'skipped' }))
    await waitFor(() => expect(within(card).getByTestId('press-status').textContent).toBe('Skipped'))
  })

  it('Replied? toggles replied', async () => {
    mockPress.patch.mockResolvedValue(pitch({ replied: true }))
    render(<PressPage />)
    const card = await screen.findByTestId('press-pitch')
    fireEvent.click(within(card).getByText('Replied?'))
    await waitFor(() => expect(mockPress.patch).toHaveBeenCalledWith('p1', { replied: true }))
    await screen.findByText('Replied ✓')
  })

  it('Got a link records the link won', async () => {
    mockPress.patch.mockResolvedValue(pitch({ link_won_url: 'https://hindustantimes.com/story' }))
    render(<PressPage />)
    const card = await screen.findByTestId('press-pitch')
    fireEvent.change(within(card).getByTestId('press-link-input'), { target: { value: 'https://hindustantimes.com/story' } })
    fireEvent.click(within(card).getByText('Got a link'))
    await waitFor(() => expect(mockPress.patch).toHaveBeenCalledWith('p1', { link_won_url: 'https://hindustantimes.com/story' }))
    await screen.findByText('https://hindustantimes.com/story')
  })
})

describe('gmailComposeUrl / mailtoUrl', () => {
  it('encode special characters safely', () => {
    const p = pitch({ subject: 'A & B', body: 'Line one\nLine two' })
    const url = new URL(gmailComposeUrl(p))
    expect(url.searchParams.get('su')).toBe('A & B')
    expect(url.searchParams.get('body')).toBe('Line one\nLine two')
    expect(mailtoUrl(p).startsWith('mailto:priya@ht.example?')).toBe(true)
  })
})
