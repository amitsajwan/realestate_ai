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
