import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import AgentDetailPage from '@/app/studio/agents/[id]/page'
import { AddAgentSheet } from '@/components/app/agents/AddAgentSheet'
import { AgentsScreen } from '@/components/app/agents/AgentsScreen'
import { NewListingFlow } from '@/components/app/NewListingFlow'
import { ApiError } from '@/lib/app/api'
import { CONSENT_TEXT, createConciergeApi, createFixtureConciergeApi, fixtureAgents, progressFraction } from '@/lib/app/concierge'
import type { ConciergeApi } from '@/lib/app/concierge'

const mockApi: Record<string, jest.Mock> = {}
const names = ['list', 'create', 'get', 'setConsent', 'createListing', 'updateListing', 'publishListing', 'getBranding', 'saveBranding', 'makePack', 'captions', 'post']
names.forEach((n) => (mockApi[n] = jest.fn()))

jest.mock('next/navigation', () => ({ useParams: () => ({ id: 'fx-a1' }), usePathname: () => '/studio/agents' }))
jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok', getSiteUrl: () => 'https://site.test', useSession: () => ({ ready: true, token: 't' }) }))
jest.mock('@/lib/app/client', () => ({
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
  api: {
    aiDraft: (...a: unknown[]) => mockAiDraft(...a),
    uploadImages: jest.fn(),
    createListing: jest.fn(() => { throw new Error('the agent API must not be used on behalf of someone') }),
  },
}))
jest.mock('@/lib/app/concierge', () => ({
  ...jest.requireActual('@/lib/app/concierge'),
  conciergeApi: new Proxy({}, { get: (_t, k: string) => (...a: unknown[]) => mockApi[k](...a) }),
}))
const mockAiDraft = jest.fn()

const FX = fixtureAgents()
const detail = (id: string) => ({ ...FX.find((a) => a.id === id)! })

beforeEach(() => {
  names.forEach((n) => mockApi[n].mockReset())
  mockApi.list.mockResolvedValue(FX.map(({ listings: _l, consent: _c, ...s }) => s))
  mockApi.get.mockImplementation(async (id: string) => detail(id))
  mockApi.getBranding.mockResolvedValue({})
  mockAiDraft.mockReset()
})

describe('Agents list', () => {
  it('shows every agent with a progress ring, masked mobile and the next step', async () => {
    render(<AgentsScreen />)
    const rows = await screen.findAllByTestId('agent-row')
    expect(rows).toHaveLength(3)
    expect(within(rows[0]).getByText('Rahul Sharma')).toBeInTheDocument()
    expect(within(rows[0]).getByRole('img', { name: '7 of 8 steps done' })).toBeInTheDocument()
    expect(within(rows[0]).getByText(/98\*{6}10/)).toBeInTheDocument()
    expect(within(rows[0]).getByText(/Next: 3 listings/)).toBeInTheDocument()
    expect(within(rows[2]).getByRole('img', { name: '0 of 8 steps done' })).toBeInTheDocument()
    expect(rows[0]).toHaveAttribute('href', '/studio/agents/fx-a1')
  })

  it('has an empty state and a friendly message when the user is not the owner', async () => {
    mockApi.list.mockResolvedValueOnce([])
    const { unmount } = render(<AgentsScreen />)
    expect(await screen.findByText(/No agents yet/)).toBeInTheDocument()
    unmount()
    mockApi.list.mockRejectedValueOnce(new Error('The Agents area is only for the owner.'))
    render(<AgentsScreen />)
    expect(await screen.findByText(/only for the owner/)).toBeInTheDocument()
  })
})

describe('Add agent flow', () => {
  it('validates, creates, then shows the code and the WhatsApp message with a copy button', async () => {
    const onCreated = jest.fn()
    mockApi.create.mockResolvedValue({
      agent: FX[2], created: true, code: '482913', reissued: false,
      whatsapp_message: 'Hi Sandeep, welcome to Avasetu! Open https://s.test/join, enter 9876543210 and your personal code 482913.',
      whatsapp_url: 'https://wa.me/919876543210?text=x',
    })
    Object.assign(navigator, { clipboard: { writeText: jest.fn().mockResolvedValue(undefined) } })
    render(<AddAgentSheet onClose={jest.fn()} onCreated={onCreated} />)
    const create = screen.getByRole('button', { name: 'Create agent' })
    expect(create).toBeDisabled()
    fireEvent.change(screen.getByLabelText(/His name/), { target: { value: 'Sandeep Patil' } })
    fireEvent.change(screen.getByLabelText(/His mobile/), { target: { value: '12345' } })
    expect(screen.getAllByText(/valid 10-digit/).length).toBeGreaterThan(0)
    expect(create).toBeDisabled()
    fireEvent.change(screen.getByLabelText(/His mobile/), { target: { value: '98765 43210' } })
    fireEvent.change(screen.getByLabelText(/Label/), { target: { value: 'Sandeep, Hinjewadi' } })
    fireEvent.click(create)
    expect(await screen.findByTestId('invite-code')).toHaveTextContent('482913')
    expect(mockApi.create).toHaveBeenCalledWith({ name: 'Sandeep Patil', mobile: '+919876543210', label: 'Sandeep, Hinjewadi', reissue: false })
    expect(onCreated).toHaveBeenCalled()
    expect((screen.getByLabelText('WhatsApp message') as HTMLTextAreaElement).value).toContain('482913')
    fireEvent.click(screen.getByRole('button', { name: 'Copy message' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Copied!' })).toBeInTheDocument())
    expect(screen.getByRole('link', { name: 'Open WhatsApp' })).toHaveAttribute('href', expect.stringContaining('wa.me/91'))
  })

  it('an agent that already exists gets no code until the owner asks for a new one', async () => {
    mockApi.create.mockResolvedValueOnce({ agent: FX[0], created: false, code: null, reissued: false, whatsapp_message: null, whatsapp_url: null })
    render(<AddAgentSheet onClose={jest.fn()} onCreated={jest.fn()} />)
    fireEvent.change(screen.getByLabelText(/His name/), { target: { value: 'Rahul Sharma' } })
    fireEvent.change(screen.getByLabelText(/His mobile/), { target: { value: '9876543210' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create agent' }))
    expect(await screen.findByText(/already added/)).toBeInTheDocument()
    expect(screen.queryByTestId('invite-code')).toBeNull()
    mockApi.create.mockResolvedValueOnce({ agent: FX[0], created: false, code: '111222', reissued: true, whatsapp_message: 'm 111222', whatsapp_url: null })
    fireEvent.click(screen.getByRole('button', { name: 'Make a new code' }))
    expect(await screen.findByTestId('invite-code')).toHaveTextContent('111222')
    expect(mockApi.create).toHaveBeenLastCalledWith(expect.objectContaining({ reissue: true }))
  })
})

describe('Agent detail', () => {
  it('shows the checklist, brand, listings, consent wording and the preview link', async () => {
    render(<AgentDetailPage />)
    expect(await screen.findByRole('heading', { name: 'Rahul Sharma' })).toBeInTheDocument()
    expect(screen.getByTestId('check-logo')).toHaveAttribute('data-done', 'true')
    expect(screen.getByTestId('check-three_listings')).toHaveAttribute('data-done', 'false')
    expect(screen.getByRole('link', { name: /Preview Rahul.s page/ })).toHaveAttribute('href', '/agent/rahul-sharma')
    expect(screen.getByRole('link', { name: 'Add listing for Rahul' })).toHaveAttribute('href', '/studio/agents/fx-a1/listings/new')
    expect(screen.getByTestId('consent-text')).toHaveTextContent(CONSENT_TEXT)
    expect(screen.getAllByTestId('agent-listing')).toHaveLength(3)
    expect(screen.getByRole('region', { name: 'Brand' })).toBeInTheDocument()
  })

  it('records consent with the exact wording through the toggle', async () => {
    mockApi.get.mockResolvedValue(detail('fx-a2'))
    mockApi.setConsent.mockResolvedValue({ text: CONSENT_TEXT, given: true })
    render(<AgentDetailPage />)
    const sw = await screen.findByRole('switch')
    expect(sw).toHaveAttribute('aria-checked', 'false')
    fireEvent.click(sw)
    await waitFor(() => expect(mockApi.setConsent).toHaveBeenCalledWith('fx-a2', true))
  })

  it('publishes a draft listing', async () => {
    mockApi.publishListing.mockResolvedValue({})
    render(<AgentDetailPage />)
    await screen.findByRole('heading', { name: 'Rahul Sharma' })
    fireEvent.click(screen.getByRole('button', { name: 'Publish' }))
    await waitFor(() => expect(mockApi.publishListing).toHaveBeenCalledWith('fx-a1', 'fx-l3'))
  })

  it('shows the exact captions first, then posts only after approval', async () => {
    const fx = createFixtureConciergeApi()
    mockApi.captions.mockImplementation((...a: Parameters<ConciergeApi['captions']>) => fx.captions(...a))
    mockApi.post.mockResolvedValue([{ channel: 'facebook_page', status: 'dry_run' }, { channel: 'instagram', status: 'dry_run' }])
    render(<AgentDetailPage />)
    await screen.findByRole('heading', { name: 'Rahul Sharma' })
    fireEvent.click(screen.getAllByRole('button', { name: 'Post to Avasetu' })[0])
    const fb = await screen.findByTestId('caption-facebook_page')
    expect(fb).toHaveTextContent('Listed by Rahul Sharma | RERA agent reg: A52100012345')
    expect(fb).toHaveTextContent(/Interested\? https:\/\//)
    expect(screen.getByTestId('caption-instagram')).toHaveTextContent('Link in our bio')
    expect(mockApi.post).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Approve and post for Rahul' }))
    await waitFor(() => expect(mockApi.post).toHaveBeenCalledWith('fx-a1', 'fx-l1'))
    expect((await screen.findAllByText(/test mode, nothing was published/)).length).toBeGreaterThan(0)
  })

  it('creates the marketing pack when the server says it is missing, and blocks posting without consent', async () => {
    mockApi.get.mockResolvedValue({ ...detail('fx-a1'), consent_given: false })
    const fx = createFixtureConciergeApi()
    mockApi.captions.mockRejectedValueOnce(new ApiError(409, 'Create the marketing pack for this listing first'))
    mockApi.captions.mockImplementation((...a: Parameters<ConciergeApi['captions']>) => fx.captions(...a))
    mockApi.makePack.mockResolvedValue(undefined)
    render(<AgentDetailPage />)
    await screen.findByRole('heading', { name: 'Rahul Sharma' })
    fireEvent.click(screen.getAllByRole('button', { name: 'Post to Avasetu' })[0])
    await screen.findByTestId('caption-facebook_page')
    expect(mockApi.makePack).toHaveBeenCalledWith('fx-a1', 'fx-l1')
    expect(screen.getByRole('alert')).toHaveTextContent(/consent first/)
    expect(screen.getByRole('button', { name: /Approve and post/ })).toBeDisabled()
  })
})

describe('Add listing on behalf of an agent', () => {
  const DRAFT = {
    draft: { transaction: 'sale', property_type: 'apartment', title: '2 BHK in Baner', price_inr: 8500000, city: 'Pune', locality: 'Baner', bhk: 2, description: { en: 'Nice 2 BHK' } },
    confidence: {}, missing: [], warnings: [],
  }

  it('creates and publishes under that agent, never through the agent API', async () => {
    mockAiDraft.mockResolvedValue(DRAFT)
    mockApi.createListing.mockResolvedValue({ id: 'L9', title: '2 BHK in Baner' })
    mockApi.publishListing.mockResolvedValue({ id: 'L9', title: '2 BHK in Baner', status: 'live' })
    render(<NewListingFlow onBehalfOf={{ id: 'fx-a1', name: 'Rahul Sharma' }} />)
    expect(screen.getByRole('heading', { name: 'Listing for Rahul' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', '/studio/agents/fx-a1')
    fireEvent.change(screen.getByLabelText(/Describe the property/), { target: { value: '2 BHK in Baner 85 lakh' } })
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    fireEvent.click(await screen.findByRole('button', { name: /skip for now/i }))
    fireEvent.click(await screen.findByRole('button', { name: /confirm/i }))
    expect(await screen.findByTestId('behalf-done')).toHaveTextContent('Saved for Rahul')
    expect(mockApi.createListing).toHaveBeenCalledWith('fx-a1', expect.objectContaining({ city: 'Pune', locality: 'Baner', price_inr: 8500000 }))
    expect(mockApi.publishListing).toHaveBeenCalledWith('fx-a1', 'L9')
    expect(screen.getByRole('link', { name: 'Back to Rahul' })).toHaveAttribute('href', '/studio/agents/fx-a1')
  })

  it('shows the server problem and retries without creating a second draft', async () => {
    mockAiDraft.mockResolvedValue(DRAFT)
    mockApi.createListing.mockResolvedValue({ id: 'L9', title: 't' })
    mockApi.publishListing.mockRejectedValueOnce(new ApiError(422, 'Price looks wrong for a sale'))
    mockApi.publishListing.mockResolvedValue({ id: 'L9', title: 't', status: 'live' })
    mockApi.updateListing.mockResolvedValue({ id: 'L9', title: 't' })
    render(<NewListingFlow onBehalfOf={{ id: 'fx-a1', name: 'Rahul Sharma' }} />)
    fireEvent.change(screen.getByLabelText(/Describe the property/), { target: { value: 'x' } })
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    fireEvent.click(await screen.findByRole('button', { name: /skip for now/i }))
    fireEvent.click(await screen.findByRole('button', { name: /confirm/i }))
    expect((await screen.findAllByText(/Price looks wrong/)).length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }))
    await screen.findByTestId('behalf-done')
    expect(mockApi.createListing).toHaveBeenCalledTimes(1)
    expect(mockApi.updateListing).toHaveBeenCalledWith('fx-a1', 'L9', expect.anything())
  })
})

describe('concierge client and fixtures', () => {
  it('calls the owner endpoints with the bearer token and surfaces 403 and 404', async () => {
    const fetchImpl = jest.fn().mockResolvedValue({ ok: true, status: 200, text: async () => JSON.stringify({ items: [] }) })
    const api = createConciergeApi({ getToken: () => 'tok', baseUrl: 'http://x', fetchImpl })
    await api.list()
    expect(fetchImpl).toHaveBeenCalledWith('http://x/api/v1/concierge/agents', expect.objectContaining({ method: 'GET', headers: expect.objectContaining({ Authorization: 'Bearer tok' }) }))
    fetchImpl.mockResolvedValueOnce({ ok: true, status: 200, text: async () => '{}' })
    await api.setConsent('a/b', true)
    const [url, init] = fetchImpl.mock.calls[1]
    expect(url).toBe('http://x/api/v1/concierge/agents/a%2Fb/consent')
    expect(JSON.parse(init.body)).toEqual({ given: true, text: CONSENT_TEXT })
    fetchImpl.mockResolvedValueOnce({ ok: false, status: 403, text: async () => JSON.stringify({ detail: 'nope' }) })
    await expect(api.list()).rejects.toMatchObject({ status: 403 })
  })

  it('fixture api walks the whole flow: add agent, consent, listing, publish, progress grows', async () => {
    const fx = createFixtureConciergeApi()
    const made = await fx.create({ name: 'Neha Joshi', mobile: '+919812345678', label: 'Neha' })
    expect(made.code).toMatch(/^\d{6}$/)
    expect(made.agent.mobile).toBe('98******78')
    await expect(fx.post(made.agent.id, 'x')).rejects.toMatchObject({ status: 409 })
    await fx.setConsent(made.agent.id, true)
    const l = await fx.createListing(made.agent.id, { title: 'Home' })
    await fx.publishListing(made.agent.id, l.id)
    const d = await fx.get(made.agent.id)
    expect(d.progress.done).toBe(2) // consent and first listing
    expect(d.checklist.find((c) => c.key === 'first_listing')!.done).toBe(true)
    expect(progressFraction({ done: 2, total: 8 })).toBe(0.25)
  })
})
