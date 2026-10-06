import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { longDay } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: (p: { topic?: string }) => <div data-testid="enquiry">{p.topic}</div> }))

const P: RegisterProject = {
  slug: 'rohan-abhilasha-4-wagholi', name: 'Rohan Abhilasha 4', regno: 'P52100080076', promoter: 'Rohan Builders', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-10-30', completion_at_registration: '2028-12-31',
  units_total: 416, units_booked: 244, details_read_at: '2026-10-03', listed_or_updated: '2026-09-28',
  maharera_url: 'https://maharerait.maharashtra.gov.in/public/project/view/80076',
  paragraph: 'Rohan Abhilasha 4 is a project by Rohan Builders in Wagholi, Pune, registered with MahaRERA as P52100080076.',
  indexable: true, same_area: [{ name: 'Kesnand Greens', slug: 'kesnand-greens-wagholi', completion_now: '2029-03-31' }], source: 'MahaRERA public records',
}

describe('Avasetu project page from the MahaRERA register', () => {
  it('shows our facts with source and date, then the official record last', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Rohan Abhilasha 4')
    expect(screen.getByTestId('paragraph')).toHaveTextContent(/registered with MahaRERA as P52100080076/)
    expect(screen.getByText('30 Oct 2029')).toBeInTheDocument()
    expect(screen.getByText(/At registration: 31 Dec 2028. MahaRERA, read 3 Oct 2026/)).toBeInTheDocument()
    expect(screen.getByText('244 of 416')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Kesnand Greens' })).toHaveAttribute('href', '/projects/kesnand-greens-wagholi')
    expect(screen.getAllByRole('link', { name: /Wagholi/ })[0]).toHaveAttribute('href', '/localities/wagholi')
    expect(screen.getByTestId('enquiry')).toHaveTextContent('Rohan Abhilasha 4 (MahaRERA P52100080076)')
    const official = screen.getByRole('link', { name: /official MahaRERA record/ })
    expect(official).toHaveAttribute('href', P.maharera_url)
    expect(within(official.closest('footer')!).getByText(/Source: MahaRERA public records/)).toBeInTheDocument()
  })

  it('a thin page says it is still filling in and shows no empty facts', () => {
    render(<RegisterProjectPage p={{ ...P, completion_now: null, completion_at_registration: null, units_total: null, units_booked: null, indexable: false, same_area: [] }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByText(/still reading this project/)).toBeInTheDocument()
    expect(screen.queryByText(/Homes booked/)).toBeNull()
  })

  it('shows the agent offer the posts quote, labelled with its source', () => {
    const facts = { offer: { property_type: 'plot', price_inr: 3230000, plot_sqft: 1000, source: "the agent's listing", read_at: '2026-10-06' } } as never
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={facts} />)
    expect(screen.getByTestId('offer')).toHaveTextContent(/plot · plot 1,000 sq ft/)
    expect(screen.getByTestId('offer')).toHaveTextContent(/From the agent's listing, 6 Oct 2026/)
  })

  it('formats days', () => {
    expect(longDay('2029-10-30')).toBe('30 Oct 2029')
    expect(longDay(null)).toBe('')
  })
})
