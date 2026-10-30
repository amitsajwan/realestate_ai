import React from 'react'
import { render } from '@testing-library/react'
import Hero from '@/components/site/Hero'
import type { AgentProfile } from '@/lib/site/types'

const base = { agent_name: 'Sharad', slug: 'house-deal', branding_data: { business_name: 'House Deal' } } as AgentProfile

describe('agent hero avatar', () => {
  it('shows the photo, else the business logo, else initials', () => {
    const logo = '/uploads/images/logo.jpg'
    const { container, rerender } = render(<Hero agent={{ ...base, branding_data: { ...base.branding_data, logo } }} city="Pune" />)
    expect(container.querySelector(`img[src="${logo}"]`)).not.toBeNull()
    rerender(<Hero agent={base} city="Pune" />)
    expect(container.querySelector(`img[src="${logo}"]`)).toBeNull()
    expect(container.textContent).toContain('SH')
  })
})

describe('agent hero with a banner that carries its own words', () => {
  it('shows the picture whole with a phone copy, and keeps the heading off the lettering', () => {
    const b = { ...base.branding_data, banner: '/uploads/images/hd-banner.jpg', banner_mobile: '/uploads/images/hd-banner-phone.jpg',
      banner_words: true, banner_alt: 'Welcome to House Deal', tagline: 'Your Dream Home, Our Best Deal' }
    const { container } = render(<Hero agent={{ ...base, branding_data: b }} city="Pune" />)
    expect(container.querySelector('section')?.getAttribute('data-hero')).toBe('words')
    expect(container.querySelector('img[src="/uploads/images/hd-banner.jpg"]')?.getAttribute('alt')).toBe('Welcome to House Deal')
    expect(container.querySelector('source')?.getAttribute('srcset')).toBe('/uploads/images/hd-banner-phone.jpg')
    expect(container.querySelector('h1')?.className).toContain('sr-only')
    expect(container.querySelector('h1')?.textContent).toBe('Your Dream Home, Our Best Deal')
    expect(container.textContent).toContain('House Deal')
  })
})
