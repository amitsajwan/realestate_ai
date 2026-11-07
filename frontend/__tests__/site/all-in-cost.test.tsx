import { render, screen, within } from '@testing-library/react'
import React from 'react'
import PriceBox from '@/components/site/PriceBox'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { allInCost, isCommercial } from '@/lib/site/allin'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <div /> }))

const amounts = (price: number, stage: 'building' | 'completion_passed', sqft?: number | null) =>
  Object.fromEntries(allInCost(price, stage, sqft).lines.map((l) => [l.key, l.amount]))

describe('the all-in cost of a price (lib/site/allin.ts)', () => {
  it('adds 5% GST, 7% stamp duty and registration capped at ₹30,000 to a home being built', () => {
    const c = allInCost(9_600_000, 'building', 750)
    expect(amounts(9_600_000, 'building', 750)).toEqual({ price: 9_600_000, gst: 480_000, stamp: 672_000, registration: 30_000 })
    expect(c.total).toBe(10_782_000)
    expect(c.gstLeftOut).toBe(false)
  })

  it('charges registration at 1% when that is under ₹30,000', () => {
    expect(amounts(2_500_000, 'building', null).registration).toBe(25_000)
  })

  it('gives the 1% affordable rate only when both the price and the size are within the limits', () => {
    expect(amounts(4_000_000, 'building', 650).gst).toBe(40_000)
    expect(amounts(4_500_000, 'building', 968).gst).toBe(45_000)        // both limits are inclusive
    expect(amounts(4_500_001, 'building', 650).gst).toBe(225_000)       // a rupee over ₹45 L
    expect(amounts(4_000_000, 'building', 969).gst).toBe(200_000)       // over 90 sq m
    expect(allInCost(4_000_000, 'building', 650).total).toBe(4_350_000)
  })

  it('does not assume the affordable rate when the size is not known, and says when it would apply', () => {
    const gst = allInCost(4_000_000, 'building', null).lines.find((l) => l.key === 'gst')!
    expect(gst.amount).toBe(200_000)
    expect(gst.note).toMatch(/1% instead if the carpet area is 90 sq m/)
    expect(allInCost(9_600_000, 'building', null).lines.find((l) => l.key === 'gst')!.note).not.toMatch(/1%/)
  })

  it('leaves GST out once the completion date has passed, because the occupancy certificate decides it', () => {
    const c = allInCost(9_600_000, 'completion_passed', 750)
    expect(c.lines.find((l) => l.key === 'gst')).toMatchObject({ amount: null, note: expect.stringMatching(/occupancy certificate/) })
    expect(c.total).toBe(9_600_000 + 672_000 + 30_000)
    expect(c.gstLeftOut).toBe(true)
  })
})

const ROW = { official: false, sources: [{ site: 'a.example', url: null }, { site: 'b.example', url: null }] }

describe('prices on a project page fold out their all-in cost', () => {
  it('shows each home size with the taxes added and the builder charges left to the cost sheet', () => {
    render(<PriceBox stage="building" prices={{ read_at: '2026-10-20', rows: [
      { ...ROW, bhk: '2 BHK', from_inr: 9_600_000, to_inr: null, sqft: 750 },
      { ...ROW, bhk: '1 BHK', from_inr: 4_000_000, to_inr: null, sqft: 650 },
    ] }} />)
    const [two, one] = screen.getAllByTestId('all-in')
    expect(two).toHaveTextContent('All-in cost of the 2 BHK at ₹96 L: about ₹1.08 Cr')
    expect(within(two).getByText('GST (5%)')).toBeInTheDocument()
    expect(within(two).getByTestId('all-in-total')).toHaveTextContent('₹1.08 Cr')
    expect(two).toHaveTextContent(/Not included: parking, club house, maintenance deposit/)
    expect(one).toHaveTextContent('All-in cost of the 1 BHK at ₹40 L: about ₹43.5 L')
    expect(within(one).getByText('GST (1%)')).toBeInTheDocument()
  })

  it('says "+ GST if any" and asks about GST when the completion date has passed', () => {
    render(<PriceBox stage="completion_passed" prices={{ read_at: null, rows: [{ ...ROW, bhk: '3 BHK', from_inr: 9_600_000, to_inr: null }] }} />)
    const box = screen.getByTestId('all-in')
    expect(box).toHaveTextContent('about ₹1.03 Cr + GST if any')
    expect(within(box).getByText('Ask')).toBeInTheDocument()
  })

  it('gives a plot no breakdown', () => {
    render(<PriceBox stage="building" prices={{ read_at: null, rows: [{ ...ROW, bhk: 'Plot', from_inr: 2_000_000, to_inr: null }] }} />)
    expect(screen.queryByTestId('all-in')).toBeNull()
  })
})

const P: RegisterProject = {
  slug: 'kesnand-greens-wagholi', name: 'Kesnand Greens', regno: 'P52100099999', promoter: 'B', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-10-30', completion_at_registration: '2029-10-30',
  units_total: 100, units_booked: 10, details_read_at: '2026-10-03', listed_or_updated: '2026-09-28',
  maharera_url: 'https://maharerait.maharashtra.gov.in/public/project/view/99999', paragraph: 'Kesnand Greens is a project in Wagholi.', indexable: true, same_area: [],
  source: 'MahaRERA public records',
  prices: { read_at: '2026-10-20', rows: [{ ...ROW, bhk: '2 BHK', from_inr: 9_600_000, to_inr: null, sqft: 750 }] },
}

describe('the register project page', () => {
  it('adds GST while the filed completion date is ahead', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(within(screen.getByTestId('prices')).getByText('GST (5%)')).toBeInTheDocument()
  })

  it('asks about GST once the completion date has passed, or before it is read', () => {
    const { unmount } = render(<RegisterProjectPage p={{ ...P, completion_passed: true }} siteUrl="https://avasetu.in" facts={null} />)
    expect(within(screen.getByTestId('prices')).getByTestId('all-in')).toHaveTextContent('+ GST if any')
    unmount()
    render(<RegisterProjectPage p={{ ...P, completion_now: null }} siteUrl="https://avasetu.in" facts={null} />)
    expect(within(screen.getByTestId('prices')).getByTestId('all-in')).toHaveTextContent('+ GST if any')
  })

  it("works out the agent's offer too, on the first home of its price sheet, but never a plot's or a rent", () => {
    const sheet = { offer: { property_type: 'apartment', price_inr: 4_000_000, source: "the agent's listing",
      homes: [{ bhk: 1, label: '1 BHK', carpet_sqft: 650, price_inr: 4_000_000 }, { bhk: 2, label: '2 BHK', carpet_sqft: 900, price_inr: 6_000_000 }] } } as never
    const { unmount } = render(<RegisterProjectPage p={{ ...P, prices: null }} siteUrl="https://avasetu.in" facts={sheet} />)
    expect(within(screen.getByTestId('offer')).getByTestId('all-in')).toHaveTextContent('All-in cost of the 1 BHK at ₹40 L: about ₹43.5 L')
    unmount()
    // a headline price that is none of the sheet's homes: no home is named and no size is assumed, so no 1% rate
    const odd = { offer: { property_type: 'apartment', price_inr: 4_000_000,
      homes: [{ bhk: 2, label: '2 BHK', carpet_sqft: 650, price_inr: 6_000_000 }, { bhk: 3, label: '3 BHK', carpet_sqft: 900, price_inr: 8_000_000 }] } } as never
    const r0 = render(<RegisterProjectPage p={{ ...P, prices: null }} siteUrl="https://avasetu.in" facts={odd} />)
    const box = within(screen.getByTestId('offer')).getByTestId('all-in')
    expect(box).toHaveTextContent('All-in cost of this home at ₹40 L')
    expect(within(box).getByText('GST (5%)')).toBeInTheDocument()
    expect(screen.getByTestId('own-cash')).not.toHaveTextContent('for the 2 BHK')
    r0.unmount()
    const plot = { offer: { property_type: 'plot', price_inr: 3_230_000, plot_sqft: 1000 } } as never
    const r1 = render(<RegisterProjectPage p={{ ...P, prices: null }} siteUrl="https://avasetu.in" facts={plot} />)
    expect(within(screen.getByTestId('offer')).queryByTestId('all-in')).toBeNull()
    r1.unmount()
    const rent = { offer: { transaction: 'rent', property_type: 'apartment', price_inr: 30_000 } } as never
    render(<RegisterProjectPage p={{ ...P, prices: null }} siteUrl="https://avasetu.in" facts={rent} />)
    expect(within(screen.getByTestId('offer')).queryByTestId('all-in')).toBeNull()
  })
})

it('a shop or office pays neither home rate: its GST is asked of the builder and stays out of the total', () => {
  const c = allInCost(5_500_000, 'building', 445, true)
  expect(c.lines.find((l) => l.key === 'gst')?.amount).toBeNull()
  expect(c.gstLeftOut).toBe(true)
  expect(c.total).toBe(5_500_000 + 385_000 + 30_000)
  expect(isCommercial('office')).toBe(true)
  expect(isCommercial('apartment')).toBe(false)
})
