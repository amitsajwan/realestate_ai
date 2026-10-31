import { fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'

const mockInquiry = jest.fn(async (..._args: unknown[]) => true)
jest.mock('@/lib/site/tracking', () => ({ submitInquiry: (...args: unknown[]) => mockInquiry(...args), trackEvent: () => {} }))
const HD_LISTING = {
  id: 'l1', status: 'live', transaction: 'sale', property_type: 'apartment', title: 'Springshire', project_name: 'Springshire',
  price_inr: 8_400_000, locality: 'Wagholi', bhk: 2, rera_no: 'P2', media: [], amenities: [], description: {}, video_count: 0,
  configurations: [{ bhk: 2, carpet_sqft: 700, price_inr: 8_400_000 }],
}
jest.mock('@/lib/site/api', () => ({
  getSitemapEntries: async () => ({ listings: [{ agent_slug: 'house-deal', id: 'l1', rera_no: 'P2' }], projects: [] }),
  getAgent: async () => ({ slug: 'house-deal', agent_name: 'Sharad', branding_data: { business_name: 'House Deal' } }),
  getListings: async () => ({ items: [HD_LISTING], total: 1 }),
  getPropertyFacts: async ({ rera }: { rera: string }) => (rera === 'P1'
    ? { nearby: [{ label: 'School', name: 'Far School', km: 2.4 }, { label: 'School', name: 'Near School', km: 0.8 }, { label: 'Hospital', name: 'City Hospital', km: 1.5 }] }
    : null),
}))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
const row = (slug: string, regno: string, place: string, extra: object = {}) => ({
  slug, regno, name: slug.toUpperCase(), area: null, place, place_name: place[0].toUpperCase() + place.slice(1), completion_now: '2029-06-30', listed_or_updated: null, indexable: true,
  units_total: 100, units_booked: 60, months_later: 0, map: { lat: 18.5632, lon: 73.9497 }, homes: [{ bhk: '2 BHK', from_inr: 9_000_000 }], ...extra,
})
jest.mock('@/lib/site/register', () => {
  const actual = jest.requireActual('@/lib/site/register')
  return {
    ...actual,
    getRegisterProjects: async () => [
      row('kharadi-heights', 'P1', 'kharadi'),
      row('springshire', 'P2', 'wagholi', { map: { lat: 18.5800, lon: 73.9800 }, homes: [] }),
      row('baner-towers', 'P3', 'baner'),
      row('sold-out-kharadi', 'P4', 'kharadi', { sold_out: true }),
      row('old-kharadi', 'P5', 'kharadi', { active: false }),
    ],
    getRegisterPlaces: async () => [
      { key: 'kharadi', slug: 'kharadi', name: 'Kharadi', zone: 'East Pune', projects: 3, indexable: 3 },
      { key: 'wagholi', slug: 'wagholi', name: 'Wagholi', zone: 'East Pune', projects: 1, indexable: 1 },
      { key: 'baner', slug: 'baner', name: 'Baner', zone: 'West Pune', projects: 1, indexable: 1 },
    ],
  }
})

import HomePlanForm from '@/components/site/homeplan/HomePlanForm'
import PlanLeadForm from '@/components/site/homeplan/PlanLeadForm'
import HomePlanPage from '@/app/home-plan/page'
import HomePlanResult from '@/app/home-plan/result/page'

const ANSWERS = { work: 'kharadi', budget: '75l-1cr', bhk: '2', kids: 'school', elders: '0' }

it('the plan lists East Pune projects still being sold, never another zone, a sold-out or a finished one', async () => {
  render(await HomePlanResult({ searchParams: Promise.resolve(ANSWERS) }))
  const picks = screen.getAllByTestId('plan-pick')
  expect(picks.map((p) => within(p).getByRole('heading', { level: 2 }).textContent)).toEqual(['KHARADI-HEIGHTS', 'SPRINGSHIRE'])
  expect(within(picks[0]).getByText('1.1 km from EON IT Park, Kharadi in a straight line')).toBeTruthy()
  // the partner's own price sheet stands for the project, and the card says whose it is
  expect(within(picks[1]).getByText('2 BHK from ₹84 L, the asking price published online')).toBeTruthy()
  expect(within(picks[1]).getByText('Listed by House Deal, a partner agent (not ranked higher for it)')).toBeTruthy()
  expect(screen.getByText('Ask which schools run buses to the society, and time the school run in the morning')).toBeTruthy()
  // school-going children: the nearest school from the pick's stored surroundings; no hospital, as parents do not live with them
  expect(within(picks[0]).getByText('Nearest school: Near School, 0.8 km in a straight line (OpenStreetMap)')).toBeTruthy()
  expect(within(picks[0]).queryByText(/Nearest hospital/)).toBeNull()
  // the plan shows with no number asked; sending it on WhatsApp is the one, optional, ask
  expect(screen.getByRole('heading', { name: 'Get this plan on WhatsApp, with today’s prices' })).toBeTruthy()
})

it('someone working in the west gets the finder for their side and an offer to plan for East Pune anyway', async () => {
  render(await HomePlanResult({ searchParams: Promise.resolve({ ...ANSWERS, work: 'west' }) }))
  expect(screen.queryAllByTestId('plan-pick')).toHaveLength(0)
  const box = screen.getByTestId('plan-not-east')
  expect(within(box).getByRole('link', { name: 'See projects that fit' }).getAttribute('href')).toBe('/projects?area=hinjawadi&budget=75l-1cr&bhk=2')
  expect(within(box).getByRole('link', { name: 'Plan for East Pune anyway' }).getAttribute('href')).toContain('work=home')
  expect(screen.getByRole('heading', { name: 'Tell me when you cover my area' })).toBeTruthy()
})

it('the public page counts the projects near each East Pune office and links ready plans; the FAQ says the same', async () => {
  const { container } = render(await HomePlanPage({ searchParams: Promise.resolve({}) }))
  const hubs = screen.getByTestId('plan-hubs')
  // Kharadi Heights (1.1 km) and Springshire (~3.6 km) are near EON; Baner is another zone, the sold-out and finished ones are not sold
  expect(within(hubs).getByText(/2 East Pune projects being sold are within 10 km of EON IT Park, Kharadi in a straight line, 2 of them with a published price\. Most are in Kharadi \(1\), Wagholi \(1\)\./)).toBeTruthy()
  expect(within(hubs).getAllByRole('link', { name: '2 BHK under ₹1 Cr near here' })[0].getAttribute('href')).toBe('/home-plan/result?work=kharadi&budget=75l-1cr&bhk=2')
  const ld = [...container.querySelectorAll('script[type="application/ld+json"]')].map((x) => JSON.parse(x.textContent || '{}'))
  const faq = ld.find((x) => x['@type'] === 'FAQPage')
  expect(faq.mainEntity[0].name).toBe('How many new projects are near EON IT Park, Kharadi?')
})

it('missing answers ask for them instead of showing a plan', async () => {
  render(await HomePlanResult({ searchParams: Promise.resolve({ work: 'kharadi' }) }))
  expect(screen.getByRole('link', { name: 'Answer the six questions' }).getAttribute('href')).toBe('/home-plan?work=kharadi')
})

describe('the form', () => {
  const tap = (name: string) => fireEvent.click(screen.getByRole('button', { name }))

  it('goes to the plan with the answers in the address and asks for no number', () => {
    const { container } = render(<HomePlanForm />)
    expect(screen.queryByLabelText('Mobile number')).toBeNull()
    tap('Kharadi (EON IT Park, WTC)'); tap('₹75 L – 1 Cr'); tap('2 BHK'); tap('School-going'); tap('No')
    const form = container.querySelector('form')!
    expect(form.getAttribute('action')).toBe('/home-plan/result')
    expect(form.getAttribute('method')).toBe('get')
    const sent = Object.fromEntries([...form.querySelectorAll('input[type="hidden"]')].map((i) => [i.getAttribute('name'), i.getAttribute('value')]))
    expect(sent).toEqual({ work: 'kharadi', budget: '75l-1cr', bhk: '2', kids: 'school', elders: '0' })
  })

  it('stops at the three needed answers', () => {
    render(<HomePlanForm />)
    tap('2 BHK')
    fireEvent.click(screen.getByRole('button', { name: 'Show my home plan' }))
    expect(screen.getByText('Please pick where you work, your budget and the size of home')).toBeTruthy()
  })
})

describe('sending the plan', () => {
  beforeEach(() => mockInquiry.mockClear())
  const A = { work: 'kharadi', budget: '75l-1cr', bhk: '2', kids: 'school', elders: false } as const

  it('sends no lead without a name, a valid mobile and consent', async () => {
    render(<PlanLeadForm answers={A} path="/home-plan/result?work=kharadi" />)
    fireEvent.click(screen.getByRole('button', { name: 'Send me this plan' }))
    expect(await screen.findByText('Please tick the box so the Avasetu team can contact you')).toBeTruthy()
    expect(mockInquiry).not.toHaveBeenCalled()
  })

  it('sends one Avasetu lead with the answers and the plan link', async () => {
    render(<PlanLeadForm answers={A} path="/home-plan/result?work=kharadi&budget=75l-1cr&bhk=2&kids=school&elders=0" />)
    fireEvent.change(screen.getByLabelText('Your name'), { target: { value: 'Priya' } })
    fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '98765 43210' } })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: 'Send me this plan' }))
    expect(await screen.findByTestId('plan-lead-done')).toBeTruthy()
    const [slug, listing, body] = mockInquiry.mock.calls[0] as [string, undefined, Record<string, unknown>]
    expect(slug).toBe('avasetu')
    expect(listing).toBeUndefined()
    expect(body).toMatchObject({ name: 'Priya', phone: '9876543210', consent: true, bhk: 2, budget_min_inr: 7_500_000, budget_max_inr: 10_000_000 })
    expect(String(body.message)).toContain('East Pune home plan: works: Kharadi (EON IT Park, WTC); 2 BHK')
    expect(String(body.message)).toContain('/home-plan/result?work=kharadi&budget=75l-1cr&bhk=2&kids=school&elders=0')
  })
})
