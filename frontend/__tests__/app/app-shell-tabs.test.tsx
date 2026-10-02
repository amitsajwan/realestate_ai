import { render, screen, within } from '@testing-library/react'
import React from 'react'
import { AppShell } from '@/components/app/AppShell'

let mockOwner = true
jest.mock('next/navigation', () => ({ usePathname: () => '/studio/admin' }))
jest.mock('@/lib/app/client', () => ({ isFixtureMode: () => false }))
jest.mock('@/components/app/agents/useIsOwner', () => ({ useIsOwner: () => mockOwner }))

describe('AppShell tabs', () => {
  it('owners get Admin as the first owner tab, before Agents, with labels small enough for 8 tabs', () => {
    mockOwner = true
    render(<AppShell><p>x</p></AppShell>)
    const links = within(screen.getByRole('navigation', { name: 'Main' })).getAllByRole('link')
    expect(links.map((l) => l.getAttribute('href'))).toEqual([
      '/studio', '/studio/listings', '/studio/interest', '/studio/newsroom', '/studio/content', '/studio/leads', '/studio/admin', '/studio/agents',
    ])
    expect(links[6]).toHaveAttribute('aria-current', 'page')
    expect(links[6].className).toContain('text-[10px]')
  })

  it('everyone else keeps the six tabs at the normal size', () => {
    mockOwner = false
    render(<AppShell><p>x</p></AppShell>)
    const links = within(screen.getByRole('navigation', { name: 'Main' })).getAllByRole('link')
    expect(links).toHaveLength(6)
    expect(links[0].className).toContain('text-xs')
  })
})
