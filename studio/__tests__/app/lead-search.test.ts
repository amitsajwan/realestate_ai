import { matchesSearch } from '@/lib/app/leads'
import type { Lead } from '@/lib/app/types'

const lead = { name: 'Sneha Kulkarni', phone: '+919890123456', requirement_line: '3 BHK · 1.2Cr-2Cr · Kharadi', message: 'Is the price negotiable?' } as Lead

describe('lead search', () => {
  it('finds by name, area, BHK, words they wrote and phone digits, every word must match', () => {
    for (const q of ['sneha', 'kharadi', '3 bhk', 'negotiable', '98901', 'sneha kharadi', '']) expect(matchesSearch(lead, q)).toBe(true)
    for (const q of ['baner', 'sneha baner', '12', '55555']) expect(matchesSearch(lead, q)).toBe(false)
  })
})
