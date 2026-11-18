// A place's "good and what to check" and a neighbour's price gap, written only from counts the page shows (lib/site/placeFacts,
// lib/site/register)
import { placeFaq, placeGoodToKnow } from '@/lib/site/placeFacts'
import { lowestPriceInr, priceGap } from '@/lib/site/register'
import type { RegisterListItem, RegisterPlace } from '@/lib/site/register'

const NOW = '2026-11-18'
const PLACE = { key: 'wagholi', slug: 'wagholi', name: 'Wagholi', projects: 94, indexable: 90, zone: 'East Pune' } as unknown as RegisterPlace

const row = (i: number, x: Partial<RegisterListItem> = {}): RegisterListItem => ({
  slug: `p${i}`, regno: `P${i}`, name: `Project ${i}`, area: 'wagholi', completion_now: '2029-06-30', listed_or_updated: null,
  indexable: true, units_total: 100, units_booked: 60, months_later: 0, stage: 'mid', ...x,
})

describe('a place: the good and what to check', () => {
  it('says builders mostly keep their dates when few moved them, and that buyers are booking', () => {
    const rows = [row(1, { months_later: 4 }), ...[2, 3, 4, 5, 6, 7, 8].map((i) => row(i))]
    const { good, check } = placeGoodToKnow(PLACE, rows, [], NOW, null)
    expect(good).toContain('Builders here mostly keep their dates: 1 of 8 projects have moved their possession date by 3 months or more.')
    expect(good).toContain('Buyers are booking here: 60% of the homes in projects being built are already booked.')
    expect(check).toEqual([])
  })

  it('puts moved dates under what to check, with the usual move, net of MahaRERA\'s order', () => {
    const rows = [row(1, { months_later: 12 }), row(2, { months_later: 24 }), row(3, { months_later: 36 }), row(4), row(5), row(6, { months_later: 2 })]
    const { check } = placeGoodToKnow(PLACE, rows, [], NOW, null)
    expect(check[0]).toBe("3 of 6 projects have moved their possession date by 3 months or more, usually by 24 months "
      + "(not counting MahaRERA's 2026 extension for all projects). See the date history on a project's page before you book.")
  })

  it('says nothing about dates with fewer than 5 projects to count', () => {
    const rows = [row(1, { months_later: 30 }), row(2), row(3)]
    const { good, check } = placeGoodToKnow(PLACE, rows, [], NOW, null)
    expect([...good, ...check].join(' ')).not.toMatch(/possession date by/)
    expect(placeFaq(PLACE, rows, [], NOW, null).map((f) => f.q)).not.toContain('Do builders in Wagholi keep their possession dates?')
  })

  it('names possession within a year, projects past their date with the OC, and open homes when few are booked', () => {
    const rows = [row(1, { completion_now: '2027-03-31', units_booked: 10 }), row(2, { stage: 'passed', completion_now: '2025-12-31', units_booked: 10 })]
    const { good, check } = placeGoodToKnow(PLACE, rows, [], NOW, null)
    expect(good).toContain('1 project has possession filed within the next 12 months.')
    expect(good).toContain('Room to choose: 180 of 200 homes in projects being built are still open.')
    expect(check).toContain('1 project is past the completion date filed with MahaRERA: ask for the occupancy certificate (OC) before you pay.')
  })

  it('answers whether builders keep their dates in the FAQ', () => {
    const rows = [row(1, { months_later: 10 }), ...[2, 3, 4, 5].map((i) => row(i))]
    const faq = placeFaq(PLACE, rows, [], NOW, null).find((f) => f.q === 'Do builders in Wagholi keep their possession dates?')
    expect(faq?.a).toContain('1 of the 5 projects being built in Wagholi whose dates we have read have moved their MahaRERA possession date by 3 months or more, usually by 10 months')
  })
})

describe('a neighbour\'s price against this project\'s', () => {
  it('says lower or higher in round lakhs, and about the same within 5%', () => {
    expect(priceGap(12000000, 9800000, 'Godrej Ivara')).toBe('Starts ₹22 L lower than Godrej Ivara')
    expect(priceGap(12000000, 15000000, 'Godrej Ivara')).toBe('Starts ₹30 L higher than Godrej Ivara')
    expect(priceGap(12000000, 12400000, 'Godrej Ivara')).toBe('About the same starting price as Godrej Ivara')
    expect(priceGap(null, 9800000, 'Godrej Ivara')).toBeNull()
    expect(priceGap(12000000, null, 'Godrej Ivara')).toBeNull()
  })

  it('works from the agent\'s offer when there is one, else the lowest published size price', () => {
    const prices = { read_at: null, rows: [{ bhk: '3 BHK', from_inr: 16000000, to_inr: null, official: true, sources: [] },
      { bhk: '2 BHK', from_inr: 12000000, to_inr: null, official: true, sources: [] }] }
    expect(lowestPriceInr({ prices } as never)).toBe(12000000)
    expect(lowestPriceInr({ prices } as never, { inr: 11500000 })).toBe(11500000)
    expect(lowestPriceInr({ prices: null } as never)).toBeNull()
  })
})
