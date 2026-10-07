import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MarketingPackView } from '@/components/app/MarketingPackView'
import { buildFixturePack } from '@/lib/app/fixtures-marketing'
import type { Listing, MarketingPack } from '@/lib/app/types'

const listing = { id: 'L1', title: '2 BHK in Baner', transaction: 'sale', property_type: 'apartment', price_inr: 8500000, city: 'Pune', locality: 'Baner', bhk: 2, status: 'live', media: [], description: { en: 'Bright flat' }, amenities: [] } as unknown as Listing

function pack(withGroup: boolean): MarketingPack {
  const p = buildFixturePack(listing, 'en', 1, 'https://site.test/agent/rahul/listings/L1', 'Rahul') as MarketingPack
  return { ...p, group: withGroup ? { post: '🏡 2 BHK in Baner\n₹85 Lakh\n✅ Available as of 30 Sep 2026\n🔗 https://site.test/x?src=fbgroup' } : null }
}

describe('group post card', () => {
  beforeEach(() => window.localStorage.clear())

  it('shows the generated text with no contact line until the agent adds their own', () => {
    render(<MarketingPackView pack={pack(true)} />)
    const box = screen.getByTestId('group-post')
    expect(box.textContent).toContain('Available as of 30 Sep 2026')
    expect(box.textContent).not.toMatch(/☎/)
  })

  it("appends the agent's own contact line, and keeps it only on this phone", () => {
    const { unmount } = render(<MarketingPackView pack={pack(true)} />)
    fireEvent.change(screen.getByLabelText(/Your contact line/), { target: { value: 'Rahul, WhatsApp 98xxxxxxxx' } })
    expect(screen.getByTestId('group-post').textContent).toMatch(/☎ Rahul, WhatsApp 98xxxxxxxx$/)
    expect(window.localStorage.getItem('pp_group_contact')).toBe('Rahul, WhatsApp 98xxxxxxxx')
    unmount()
    render(<MarketingPackView pack={pack(true)} />)
    expect(screen.getByLabelText(/Your contact line/)).toHaveValue('Rahul, WhatsApp 98xxxxxxxx')
  })

  it('is hidden for packs made before this existed', () => {
    render(<MarketingPackView pack={pack(false)} />)
    expect(screen.queryByTestId('card-group')).toBeNull()
  })
})

import { sourceLabel } from '@/lib/app/leads'

describe('lead sources from the new channels read naturally', () => {
  it('labels groups, comments and chat', () => {
    expect(sourceLabel('fbgroup')).toBe('Facebook group')
    expect(sourceLabel('facebook_comment')).toBe('Facebook comment')
    expect(sourceLabel('chat')).toBe('Website chat')
  })
})
