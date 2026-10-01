import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

jest.mock('@/lib/interest/api', () => ({
  ...jest.requireActual('@/lib/interest/api'),
  getInterest: jest.fn(),
  getHub: jest.fn(),
}))
jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NEXT_NOT_FOUND') } }))

import { getHub, getInterest } from '@/lib/interest/api'
import InterestPage, { generateMetadata } from '@/app/i/[code]/page'
import InterestActions from '@/app/i/[code]/InterestActions'
import GoPage from '@/app/go/page'

const subject = (over = {}) => ({
  code: 'abc2345', kind: 'listing', channel: 'facebook', title: '2BHK in Baner', subtitle: 'Ready to move', locality: 'Baner',
  image_url: '/img/a.jpg', agent_name: 'Rahul Sharma', sample: false, consent_wording: 'I agree to be contacted about this by the agent.', ...over,
})
const render1 = async (q: Record<string, string> = {}) =>
  render(await InterestPage({ params: Promise.resolve({ code: 'abc2345' }), searchParams: Promise.resolve(q) }))

describe('/i/[code] landing', () => {
  beforeEach(() => {
    ;(getInterest as jest.Mock).mockResolvedValue(subject())
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
  })

  it('server-renders the subject and the big primary button', async () => {
    await render1()
    expect(screen.getByRole('heading', { level: 1, name: '2BHK in Baner' })).toBeInTheDocument()
    expect(screen.getByText('Baner, Pune')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'I am interested' })).toBeInTheDocument()
  })

  it('the base action is a plain form post that works without JavaScript', async () => {
    const { container } = await render1()
    const form = container.querySelector('form') as HTMLFormElement
    expect(form.getAttribute('method')).toBe('post')
    expect(form.getAttribute('action')).toBe('/i/abc2345/tap')
  })

  it('labels a sample home clearly', async () => {
    ;(getInterest as jest.Mock).mockResolvedValue(subject({ sample: true }))
    await render1()
    expect(screen.getByText('SAMPLE HOME')).toBeInTheDocument()
  })

  it('404s an unknown code', async () => {
    ;(getInterest as jest.Mock).mockResolvedValue(null)
    await expect(render1()).rejects.toThrow('NEXT_NOT_FOUND')
  })

  it('shows the confirmation and the optional form after the done flag (no JS)', async () => {
    await render1({ done: '1' })
    expect(screen.getByRole('status')).toHaveTextContent(/noted your interest/i)
    expect(screen.getByLabelText(/mobile number/i)).toBeInTheDocument()
  })

  it('has an og share preview with an absolute image', async () => {
    const meta: any = await generateMetadata({ params: Promise.resolve({ code: 'abc2345' }), searchParams: Promise.resolve({}) })
    expect(meta.openGraph.title).toContain('2BHK in Baner')
    expect(meta.openGraph.images[0].url).toMatch(/^https?:\/\/.+\/img\/a\.jpg$/)
    expect(meta.robots.index).toBe(false)
  })
})

describe('InterestActions', () => {
  const props = { code: 'abc2345', agentName: 'Rahul Sharma', sample: false, consentWording: 'I agree to be contacted about this by the agent.' }
  beforeEach(() => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
  })

  it('records a click on view, then a one-tap interest with no personal fields', async () => {
    render(<InterestActions {...props} />)
    await waitFor(() => expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe('/api/v1/public/interest/abc2345/click'))
    fireEvent.click(screen.getByRole('button', { name: 'I am interested' }))
    expect(await screen.findByRole('status')).toHaveTextContent(/noted your interest/i)
    const [url, init] = (global.fetch as jest.Mock).mock.calls[1]
    expect(url).toBe('/api/v1/public/interest/abc2345')
    const body = JSON.parse(init.body)
    expect(body.name).toBeUndefined()
    expect(body.phone).toBeUndefined()
    expect(body.anon_id).toBeTruthy()
  })

  it('does not send contact details without the consent tick', async () => {
    render(<InterestActions {...props} initialStep="tapped" />)
    fireEvent.change(screen.getByLabelText(/mobile number/i), { target: { value: '9876543210' } })
    fireEvent.click(screen.getByRole('button', { name: /send my details/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/tick the box/i)
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('sends details with consent and the empty honeypot, then says they are saved', async () => {
    render(<InterestActions {...props} initialStep="tapped" />)
    fireEvent.change(screen.getByLabelText(/your name/i), { target: { value: 'Asha' } })
    fireEvent.change(screen.getByLabelText(/mobile number/i), { target: { value: '9876543210' } })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: /send my details/i }))
    expect(await screen.findByText(/details are saved/i)).toBeInTheDocument()
    const body = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)
    expect(body).toMatchObject({ name: 'Asha', phone: '9876543210', consent: true, website: '' })
  })

  it('shows a friendly message when rate limited', async () => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: false, status: 429 })
    render(<InterestActions {...props} />)
    fireEvent.click(screen.getByRole('button', { name: 'I am interested' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/too many tries/i)
  })
})

describe('/go hub', () => {
  const hub = (n: number, sample = false) => ({
    brand: 'PUNE Property', line: 'Homes and guides', links: { website: 'https://site.test', invite: 'https://site.test/request-invite', facebook: 'https://facebook.com/p', instagram: 'https://instagram.com/p' },
    items: Array.from({ length: n }, (_, i) => ({ kind: 'listing', ref: 'r' + i, title: 'Home ' + i, subtitle: 'sub', image_url: '/i.jpg', interest_code: 'code' + i, permalink: i === 0 ? 'https://fb.test/1' : null, sample })),
  })

  it('renders tappable cards with interest links and the page links', async () => {
    ;(getHub as jest.Mock).mockResolvedValue(hub(3))
    render(await GoPage())
    const buttons = screen.getAllByRole('link', { name: 'I am interested' })
    expect(buttons).toHaveLength(3)
    expect(buttons[0]).toHaveAttribute('href', '/i/code0')
    expect(screen.getByRole('link', { name: 'Visit the website' })).toHaveAttribute('href', 'https://site.test')
    expect(screen.getByRole('link', { name: 'Facebook Page' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Instagram' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'See the post' })).toHaveAttribute('href', 'https://fb.test/1')
    expect(screen.getByRole('link', { name: 'Request an invite' })).toHaveAttribute('href', 'https://site.test/request-invite')
  })

  it('labels sample homes', async () => {
    ;(getHub as jest.Mock).mockResolvedValue(hub(2, true))
    render(await GoPage())
    expect(screen.getAllByText('SAMPLE HOME')).toHaveLength(2)
  })

  it('still renders when the API is down', async () => {
    ;(getHub as jest.Mock).mockResolvedValue(null)
    render(await GoPage())
    expect(screen.getByRole('link', { name: 'Visit the website' })).toBeInTheDocument()
    expect(screen.getByText(/on the way/i)).toBeInTheDocument()
  })
})
