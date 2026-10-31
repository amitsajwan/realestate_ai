import { render, screen } from '@testing-library/react'
import React from 'react'
import BuilderLogoMark from '@/components/site/BuilderLogoMark'

// The builder's logo on the builders list and builder pages (owner 2026-10-31)
describe("a builder's logo mark", () => {
  it('shows the logo on white, named for the builder', () => {
    render(<BuilderLogoMark name="Rohan Builders" logo={{ url: '/uploads/builder_logos/rohan.png', width: 300, height: 90, tone: 'dark', site: 'rohan.com' }} />)
    expect(screen.getByRole('img', { name: 'Rohan Builders logo' })).toHaveAttribute('src', '/uploads/builder_logos/rohan.png')
    expect(screen.getByTestId('builder-logo')).toHaveClass('bg-white')
  })

  it('puts a logo drawn for a dark header on navy', () => {
    render(<BuilderLogoMark name="Kolte Patil" logo={{ url: '/uploads/builder_logos/kp.png', width: 200, height: 80, tone: 'light', site: null }} />)
    expect(screen.getByTestId('builder-logo')).toHaveClass('bg-[#16305a]')
  })
})
