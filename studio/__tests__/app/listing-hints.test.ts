import { listingHints } from '@/lib/app/listingHints'

const found = (text: string) => listingHints(text).filter((h) => h.found).map((h) => h.key)

describe('Add listing hints', () => {
  it('ticks each fact an agent typically writes', () => {
    expect(found('2 BHK Kharadi 85 lakh ready to move, 950 sq ft carpet')).toEqual(['type', 'area', 'price', 'size', 'possession'])
    expect(found('3bhk in Wakad 1.2 cr possession dec 2027')).toEqual(['type', 'area', 'price', 'possession'])
    expect(found('Shop near Phoenix mall ₹45,00,000')).toEqual(['type', 'area', 'price'])
  })

  it('an empty box ticks nothing, and "lakh" alone is not a price', () => {
    expect(found('')).toEqual([])
    expect(found('lakh')).toEqual([])
  })
})
