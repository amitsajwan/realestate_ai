import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import HiddenPhone, { hidePhone } from '@/components/site/HiddenPhone'
import { agentJsonLd, listingJsonLd } from '@/lib/site/seo'
import { shownPhone } from '@/lib/site/links'

jest.mock('@/lib/site/tracking', () => ({ trackEvent: jest.fn() }))

it("keeps the agent's number out of the page until a buyer taps to see it", () => {
  const { container } = render(<HiddenPhone code={hidePhone('917447212121')} agentSlug="house-deal" />)
  expect(container.innerHTML).not.toMatch(/7447|74472/)
  fireEvent.click(screen.getByRole('button', { name: 'Show phone number' }))
  const call = screen.getByRole('link', { name: '+91 74472 12121' })
  expect(call).toHaveAttribute('href', 'tel:+917447212121')
  expect(call.closest('[data-nosnippet]')).not.toBeNull()
})

it('gives the page the number only reversed, and never puts it in the structured data', () => {
  const agent = { slug: 'house-deal', agent_name: 'House Deal', phone: '+919921993099',
    branding_data: { show_phone: true, office_phone: '+917447212121' } } as never
  expect(shownPhone(agent)).toBe(hidePhone('917447212121'))
  const listing = { id: 'l1', title: 'x', locality: 'Kharadi', city: 'Pune', price_inr: 1, status: 'live', media: [], description: { en: '' } } as never
  expect(JSON.stringify([agentJsonLd(agent, 'Pune'), listingJsonLd(agent, listing)])).not.toMatch(/telephone|7447|9921/)
})
