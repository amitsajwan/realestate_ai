import { displayPhone, formatInr, formatPrice, groupIndian, normalizePhone, parseInr, timeAgo, waDigits } from '@/lib/app/format'

describe('formatInr', () => {
  it('formats lakh and crore per the contract', () => {
    expect(formatInr(8_500_000)).toBe('85 L')
    expect(formatInr(12_500_000)).toBe('1.25 Cr')
    expect(formatInr(10_000_000)).toBe('1 Cr')
    expect(formatInr(150_000)).toBe('1.5 L')
  })
  it('groups small amounts the Indian way', () => {
    expect(formatInr(45_000)).toBe('45,000')
    expect(formatInr(999)).toBe('999')
    expect(groupIndian(8_500_000)).toBe('85,00,000')
    expect(groupIndian(123_456_789)).toBe('12,34,56,789')
  })
  it('handles empty and rent', () => {
    expect(formatInr(null)).toBe('')
    expect(formatPrice(45_000, true)).toBe('₹45,000/mo')
    expect(formatPrice(8_500_000)).toBe('₹85 L')
  })
})

describe('parseInr', () => {
  it.each([
    ['85 lakh', 8_500_000],
    ['85 Lakhs', 8_500_000],
    ['85L', 8_500_000],
    ['1.2cr', 12_000_000],
    ['1.25 crore', 12_500_000],
    ['₹85,00,000', 8_500_000],
    ['8500000', 8_500_000],
    ['50k', 50_000],
    ['Rs. 45,000', 45_000],
  ])('parses %s', (input, expected) => {
    expect(parseInr(input)).toBe(expected)
  })
  it('returns null for junk', () => {
    expect(parseInr('')).toBeNull()
    expect(parseInr('abc')).toBeNull()
    expect(parseInr('5 bananas')).toBeNull()
    expect(parseInr(null)).toBeNull()
  })
  it('round trips to integers', () => {
    expect(Number.isInteger(parseInr('1.1 cr'))).toBe(true)
    expect(parseInr(formatInr(12_500_000))).toBe(12_500_000)
  })
})

describe('phone', () => {
  it.each(['9876543210', '+91 98765 43210', '098765-43210', '919876543210', '+91-9876543210'])('normalises %s', (raw) => {
    expect(normalizePhone(raw)).toBe('+919876543210')
  })
  it.each(['12345', '5876543210', '', '98765432101234', 'abcdefghij'])('rejects %s', (raw) => {
    expect(normalizePhone(raw)).toBeNull()
  })
  it('displays and builds wa digits', () => {
    expect(displayPhone('9876543210')).toBe('+91 98765 43210')
    expect(waDigits('+919876543210')).toBe('919876543210')
  })
})

describe('timeAgo', () => {
  const now = new Date('2026-01-01T12:00:00Z')
  it('renders relative times, treating naive datetimes as UTC', () => {
    expect(timeAgo('2026-01-01T11:59:40Z', now)).toBe('just now')
    expect(timeAgo('2026-01-01T09:59:00', now)).toBe('2h ago')
    expect(timeAgo('2025-12-29T12:00:00Z', now)).toBe('3d ago')
  })
})
