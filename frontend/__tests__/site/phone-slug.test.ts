import { isValidIndianMobile, normalizeIndianMobile, waNumber } from '@/lib/site/phone'
import { agentPath, normalizeSlug, resolveAgentSlug, slugFromHost } from '@/lib/site/slug'

describe('Indian mobile validator', () => {
  it.each(['9876543210', '+91 98765 43210', '919876543210', '09876543210', '6000000000', '98765-43210'])('accepts %s', (v) => {
    expect(isValidIndianMobile(v)).toBe(true)
  })
  it.each(['', '5876543210', '987654321', '98765432101', 'abcdefghij', '+1 9876543210'])('rejects %s', (v) => {
    expect(isValidIndianMobile(v)).toBe(false)
  })
  it('normalizes to 10 digits and wa number', () => {
    expect(normalizeIndianMobile('+91 98765 43210')).toBe('9876543210')
    expect(waNumber('9876543210')).toBe('919876543210')
    expect(waNumber(null)).toBeNull()
  })
})

describe('slug / host helper', () => {
  it('normalizes slugs', () => {
    expect(normalizeSlug('Priya-Pune')).toBe('priya-pune')
    expect(normalizeSlug('bad slug')).toBeNull()
    expect(normalizeSlug('../etc')).toBeNull()
    expect(normalizeSlug('%E0%A4%A')).toBeNull()
    expect(normalizeSlug('')).toBeNull()
  })
  it('extracts subdomain slug', () => {
    expect(slugFromHost('priya.example.in', 'example.in')).toBe('priya')
    expect(slugFromHost('priya.example.in:3000', 'example.in')).toBe('priya')
    expect(slugFromHost('example.in', 'example.in')).toBeNull()
    expect(slugFromHost('www.example.in', 'example.in')).toBeNull()
    expect(slugFromHost('a.b.example.in', 'example.in')).toBeNull()
    expect(slugFromHost('priya.other.com', 'example.in')).toBeNull()
    expect(slugFromHost('priya.example.in', undefined)).toBeNull()
  })
  it('path slug wins over host', () => {
    expect(resolveAgentSlug({ pathSlug: 'a', host: 'b.example.in', rootDomain: 'example.in' })).toBe('a')
    expect(resolveAgentSlug({ host: 'b.example.in', rootDomain: 'example.in' })).toBe('b')
  })
  it('agentPath', () => {
    expect(agentPath('x')).toBe('/agent/x')
    expect(agentPath('x', 'listings/1')).toBe('/agent/x/listings/1')
  })
})
