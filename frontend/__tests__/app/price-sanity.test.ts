import { parseInr } from '@/lib/app/format'
import { priceSanity } from '@/lib/app/validate'

const flat = (price: number, extra = {}) => ({ transaction: 'sale' as const, property_type: 'apartment' as const, bhk: 2, price_inr: price, ...extra })

describe('priceSanity (a 100x typo must not go live unnoticed)', () => {
  it('is quiet for normal prices', () => {
    expect(priceSanity(flat(8_500_000))).toBeNull()
    expect(priceSanity(flat(45_000_000, { bhk: 3 }))).toBeNull()
    expect(priceSanity({})).toBeNull()
    expect(priceSanity({ price_inr: 0 })).toBeNull()
  })

  it('catches 85 crore for a 2 BHK flat and suggests 85 lakh', () => {
    const w = priceSanity(flat(parseInr('85 cr')!))
    expect(w).toMatch(/very high for a 2 BHK apartment/)
    expect(w).toMatch(/Did you mean ₹85 L\?/)
  })

  it('catches a bare "85" (rupees) and a tiny sale price', () => {
    expect(priceSanity(flat(parseInr('85')!))).toMatch(/very low/)
  })

  it('does not nag about a genuinely large home, but still flags absurd values', () => {
    expect(priceSanity(flat(150_000_000, { bhk: 5 }))).toBeNull() // 15 Cr, 5 BHK
    expect(priceSanity(flat(150_000_000, { property_type: 'villa', bhk: 5 }))).toBeNull()
    expect(priceSanity(flat(1_200_000_000, { property_type: 'villa', bhk: 5 }))).toMatch(/very high/)
  })

  it('checks rent per month', () => {
    expect(priceSanity({ transaction: 'rent', price_inr: 25_000 })).toBeNull()
    expect(priceSanity({ transaction: 'rent', price_inr: 25_00_000 })).toMatch(/unusual/)
    expect(priceSanity({ transaction: 'rent', price_inr: 500 })).toMatch(/unusual/)
  })
})
