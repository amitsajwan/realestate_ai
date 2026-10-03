import React from 'react'
import { render, screen } from '@testing-library/react'
import DemoRibbon, { previewNote } from '@/app/agent/[slug]/DemoRibbon'
import ProjectCard from '@/components/site/ProjectCard'
import ProjectsSection from '@/components/site/ProjectsSection'
import ReraBox from '@/components/site/ReraBox'
import { bhkRange, formatDay, mapsLink, minPerSqft, monthsBetween, possessionLines, priceRange, sourceLabel } from '@/lib/site/projects'
import { isPreviewAgent, projectMetadata, withPreview } from '@/lib/site/seo'
import type { AgentProfile, PublicProject } from '@/lib/site/types'

const P: PublicProject = {
  id: 'x1', slug: 'goyal-my-home', name: 'Goyal My Home', builder: 'Goyal Properties', locality: 'Upper Kharadi',
  address: 'Nagar Road', pincode: '412207', rera_no: 'P52100078796', scope_note: 'One tower of 143 homes.',
  configurations: [
    { label: '2 BHK', bhk: 2, carpet_sqft: 941, price_inr: 9700000, price_per_sqft: 10308, source: 'agent' },
    { label: '3 BHK', bhk: 3, carpet_sqft: 1205, price_inr: 12500000, price_per_sqft: 10373, source: 'agent' },
  ],
  price_min: 9700000, price_max: 12500000, bhk_options: [2, 3], possession_target: '2028-03',
  positioning: 'One tower next to Decathlon.', who_it_suits: [], highlights: [], amenities: [], specs: {}, provenance: {},
  nearby: [], place: null, maps_query: 'My Home Upper Kharadi', media: [],
  rera: {
    regno: 'P52100078796', name: 'MY HOME UPPER KHARADI', promoter: 'GODIVA PROMOTERS LLP', project_type: 'Residential',
    registered_on: '2025-01-13', completion_at_registration: '2028-12-31', completion_now: '2029-04-30',
    units_total: 143, units_booked: 102, url: 'https://maharerait.maharashtra.gov.in/public/project/view/53311', checked_at: '2026-10-03',
  },
  booked_pct: 71, completion_moved_months: 4,
}

const AGENT = { agent_name: 'House Deal', slug: 'house-deal', branding_data: { preview: true, business_name: 'House Deal' } } as AgentProfile

describe('project helpers', () => {
  it('formats dates, prices and BHK ranges', () => {
    expect(formatDay('2029-04-30')).toBe('30 Apr 2029')
    expect(formatDay('2028-03')).toBe('Mar 2028')
    expect(formatDay('March 2028')).toBe('')
    expect(priceRange(P)).toBe('₹97 L – ₹1.25 Cr')
    expect(priceRange({ price_min: 6600000, price_max: 6600000 })).toBe('₹66 L')
    expect(bhkRange([2, 3])).toBe('2 & 3 BHK')
    expect(bhkRange([2, 2.5, 3])).toBe('2, 2.5 & 3 BHK')
    expect(monthsBetween('2028-03', '2029-04-30')).toBe(13)
    expect(minPerSqft(P)).toBe(10308)
  })

  it('explains possession without calling a project late', () => {
    const lines = possessionLines(P, 'House Deal')
    expect(lines[0]).toBe("Builder's target: Mar 2028 (as quoted by House Deal).")
    expect(lines.join(' ')).toContain('Date filed with MahaRERA: 30 Apr 2029')
    expect(lines.join(' ')).toContain('it has since moved to 30 Apr 2029')
    expect(lines.join(' ')).toContain('about 13 months apart')
    expect(lines.join(' ').toLowerCase()).not.toMatch(/\b(late|delayed)\b/)
    expect(possessionLines({ ...P, rera: null }, 'House Deal')).toHaveLength(1)
  })

  it('labels sources and never invents a map pin', () => {
    expect(sourceLabel('agent', 'House Deal')).toBe('As quoted by House Deal')
    expect(sourceLabel('maharera', 'x')).toBe('MahaRERA record')
    expect(mapsLink(P)).toBe('https://www.google.com/maps/search/?api=1&query=My%20Home%20Upper%20Kharadi')
    expect(mapsLink({ ...P, place: { lat: 18.594, lon: 73.968, source: 'osm', note: '' } })).toContain('query=18.594,73.968')
  })
})

describe('preview sites', () => {
  it('are noindex and say they are a preview', () => {
    expect(isPreviewAgent(AGENT)).toBe(true)
    expect(isPreviewAgent({ branding_data: { demo: true } })).toBe(false)
    expect(withPreview(AGENT, { title: 't' }).robots).toEqual({ index: false, follow: false })
    expect(withPreview({ ...AGENT, branding_data: {} }, { title: 't' }).robots).toBeUndefined()
    expect(projectMetadata(AGENT, P, '₹97 L').robots).toEqual({ index: false, follow: false })
    render(<DemoRibbon agent={AGENT} />)
    expect(screen.getByTestId('preview-note')).toHaveTextContent(previewNote('House Deal'))
    expect(screen.queryByTestId('demo-ribbon')).toBeNull()
  })
})

describe('project components', () => {
  it('card shows price, MahaRERA date and bookings, and links to the project', () => {
    render(<ProjectCard agentSlug="house-deal" p={P} />)
    const card = screen.getByTestId('project-card')
    expect(card).toHaveAttribute('href', '/agent/house-deal/projects/goyal-my-home')
    expect(card).toHaveTextContent('₹97 L – ₹1.25 Cr')
    expect(card).toHaveTextContent('30 Apr 2029')
    expect(card).toHaveTextContent('71%')
  })

  it('card without a MahaRERA reading says it is being checked', () => {
    render(<ProjectCard agentSlug="house-deal" p={{ ...P, rera: null, booked_pct: null }} />)
    expect(screen.getByTestId('project-card')).toHaveTextContent('Being checked')
  })

  it('section renders nothing without projects and links to compare with several', () => {
    const { container, rerender } = render(<ProjectsSection agentSlug="house-deal" projects={[]} />)
    expect(container).toBeEmptyDOMElement()
    rerender(<ProjectsSection agentSlug="house-deal" projects={[P, { ...P, slug: 'b' }]} />)
    expect(screen.getByRole('link', { name: /compare side by side/i })).toHaveAttribute('href', '/agent/house-deal/projects/compare')
  })

  it('MahaRERA box shows the record with its date and link', () => {
    render(<ReraBox p={P} />)
    expect(screen.getByText('GODIVA PROMOTERS LLP')).toBeInTheDocument()
    expect(screen.getByText('102 of 143 (71%)')).toBeInTheDocument()
    expect(screen.getByText(/3 Oct 2026/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /see the record on maharera/i })).toHaveAttribute('href', P.rera!.url)
  })
})
