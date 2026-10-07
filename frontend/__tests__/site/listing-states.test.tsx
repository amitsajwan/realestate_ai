import React from 'react'
import { render, screen } from '@testing-library/react'
import ListingBrowser from '@/components/site/ListingBrowser'
import AgentStrip from '@/components/marketing/AgentStrip'
import { FIXTURE_LISTINGS } from '@/lib/site/fixtures'

describe('agent site listing states', () => {
  it('explains sample homes when any listing is a sample', () => {
    const items = [{ ...FIXTURE_LISTINGS[0], title: 'Sample: 2 BHK in Baner' }, ...FIXTURE_LISTINGS.slice(1)]
    render(<ListingBrowser slug="amit-sajwan" items={items} />)
    expect(screen.getByText(/they are not for sale/i)).toBeInTheDocument()
  })

  it('shows no sample note for real listings only', () => {
    const items = FIXTURE_LISTINGS.map((l) => ({ ...l, title: 'Real 2 BHK in Baner' }))
    render(<ListingBrowser slug="amit-sajwan" items={items} />)
    expect(screen.queryByText(/they are not for sale/i)).toBeNull()
  })

  it('has a useful empty state with a way to enquire', () => {
    render(<ListingBrowser slug="amit-sajwan" items={[]} />)
    expect(screen.getByText(/new homes are being added/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /i'm interested/i })).toHaveAttribute('href', '#enquire')
  })
})

describe('AgentStrip', () => {
  it('invites agents to claim the free trial with no invented numbers', () => {
    const { container } = render(<AgentStrip />)
    expect(screen.getByRole('link', { name: /claim your free trial/i })).toHaveAttribute('href', '/trial')
    expect(container.textContent).not.toMatch(/\d/)
  })
})
