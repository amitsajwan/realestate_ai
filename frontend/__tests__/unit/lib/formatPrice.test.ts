import { formatPrice } from '@/lib/formatters'

describe('formatPrice', () => {
  it('should return "Contact for price" for null or undefined', () => {
    expect(formatPrice(null)).toBe('Contact for price')
    expect(formatPrice(undefined)).toBe('Contact for price')
  })

  it('should return "Contact for price" for zero', () => {
    expect(formatPrice(0)).toBe('Contact for price')
  })

  it('should format prices in crores for values >= 1 crore', () => {
    expect(formatPrice(10000000)).toBe('₹1.0Cr')
    expect(formatPrice(15000000)).toBe('₹1.5Cr')
    expect(formatPrice(25000000)).toBe('₹2.5Cr')
  })

  it('should format prices in lakhs for values >= 1 lakh but < 1 crore', () => {
    expect(formatPrice(100000)).toBe('₹1L')
    expect(formatPrice(500000)).toBe('₹5L')
    expect(formatPrice(1500000)).toBe('₹15L')
    expect(formatPrice(9999999)).toBe('₹100L')
  })

  it('should format prices with commas for values < 1 lakh', () => {
    expect(formatPrice(1000)).toBe('₹1,000')
    expect(formatPrice(50000)).toBe('₹50,000')
    expect(formatPrice(99999)).toBe('₹99,999')
  })

  it('should handle decimal values correctly', () => {
    expect(formatPrice(1000000.5)).toBe('₹10L')
    expect(formatPrice(15000000.7)).toBe('₹1.5Cr')
  })

  it('should handle edge cases', () => {
    expect(formatPrice(1)).toBe('₹1')
    expect(formatPrice(99999)).toBe('₹99,999')
    expect(formatPrice(100000)).toBe('₹1L')
    expect(formatPrice(10000000)).toBe('₹1.0Cr')
  })
})
