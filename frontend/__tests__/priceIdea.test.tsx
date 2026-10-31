import { bandText } from '@/components/site/PriceIdea'

describe('bandText', () => {
  it('says a band once with its unit, as a rough guide', () => {
    expect(bandText({ low: 22_000_000, high: 26_000_000 })).toBe('about ₹2.2 – 2.6 Cr')
    expect(bandText({ low: 7_000_000, high: 8_000_000 })).toBe('about ₹70 – 80 L')
  })
  it('keeps both units when the band crosses a crore', () => {
    expect(bandText({ low: 9_000_000, high: 11_000_000 })).toBe('about ₹90 L – ₹1.1 Cr')
  })
})
