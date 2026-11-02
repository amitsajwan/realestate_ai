import React from 'react'
import { render, screen, within } from '@testing-library/react'
import { ComingSoonView, inComingSoonZone } from '@/components/site/ComingSoonBand'
import type { UpcomingBrief } from '@/lib/site/hubs'
import type { RegisterPlace } from '@/lib/site/register'

const u = (slug: string, area_slug: string, logo = ''): UpcomingBrief => ({
  slug, name: slug, builder: 'A builder', logo, area: area_slug, area_name: area_slug, area_slug, note: '2 & 3 BHK · coming soon',
})
const place = (slug: string, zone: string) => ({ key: slug.replace(/-/g, '_'), slug, name: slug, zone, projects: 1, indexable: 1 }) as RegisterPlace

describe('coming-soon band', () => {
  it('runs on East Pune places by slug or key, and nowhere else', () => {
    const places = [place('upper-kharadi', 'East Pune'), place('baner', 'West Pune')]
    expect(inComingSoonZone(places, 'upper-kharadi')).toBe(true)
    expect(inComingSoonZone(places, 'upper_kharadi')).toBe(true)
    expect(inComingSoonZone(places, 'baner')).toBe(false)
    expect(inComingSoonZone(places, undefined)).toBe(false)
  })

  it('says not registered, takes no booking, and puts the page own area first', () => {
    render(<ComingSoonView items={[u('one', 'wagholi'), u('two', 'upper-kharadi')]} place="upper-kharadi" />)
    const band = screen.getByTestId('coming-soon-band')
    expect(band).toHaveTextContent('Not yet registered with MahaRERA')
    expect(band).toHaveTextContent('no bookings are taken')
    expect(band).not.toHaveTextContent('₹')
    const links = within(band).getAllByRole('link')
    expect(links.map((l) => l.getAttribute('href'))).toEqual(['/projects/upcoming/two#enquire', '/projects/upcoming/one#enquire'])
  })

  it('shows the builder name when there is no logo, and nothing when no project is coming', () => {
    const { container, rerender } = render(<ComingSoonView items={[u('one', 'wagholi')]} />)
    expect(screen.getByText('A builder')).toBeInTheDocument()
    rerender(<ComingSoonView items={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})
