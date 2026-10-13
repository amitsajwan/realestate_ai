import React from 'react'
import { render, screen } from '@testing-library/react'
import ProjectDetails from '@/components/site/ProjectDetails'
import type { PublicProject } from '@/lib/site/types'

jest.mock('@/components/site/ReraBox', () => ({ __esModule: true, default: () => <div data-testid="rera-box" /> }))
jest.mock('@/components/site/RegistrationsBox', () => ({ __esModule: true, default: () => <div data-testid="registrations-box" /> }))
jest.mock('@/components/site/SlideStrip', () => ({ __esModule: true, default: ({ label }: { label: string }) => <div>{label}</div> }))

const project: PublicProject = {
  id: 'p1',
  slug: 'lodha-camelot-kharadi',
  name: 'Lodha Camelot',
  builder: 'Lodha',
  locality: 'Kharadi',
  address: 'Upper Kharadi, Pune',
  pincode: '411014',
  rera_no: 'P52100012345',
  scope_note: 'Project info.',
  configurations: [{ label: '3 BHK', bhk: 3, carpet_sqft: 1240, price_inr: 21900000, price_per_sqft: 17661, source: 'agent' }],
  bhk_options: [3],
  positioning: 'A modern lifestyle address in Upper Kharadi.',
  who_it_suits: [],
  highlights: [],
  amenities: ['Clubhouse'],
  specs: { 'Status': 'Under construction' },
  provenance: { builder: 'builder' },
  nearby: [],
  maps_query: 'Lodha Camelot Kharadi Pune',
  media: [
    { url: 'https://example.com/hero.jpg', caption: 'Front elevation', credit: 'Lodha', artist_impression: false, kind: 'image' },
    { url: 'https://example.com/intro.mp4', caption: 'Project walk-through', credit: 'Lodha', artist_impression: false, kind: 'video' },
  ],
  brochure_url: 'https://example.com/brochure.pdf',
  floor_plan_url: 'https://example.com/floor-plan.pdf',
  virtual_tour_url: 'https://example.com/tour',
  emi_calculator_url: 'https://example.com/emi',
  video_url: 'https://example.com/overview.mp4',
}

describe('ProjectDetails', () => {
  it('renders linked project resources and video blocks when present', () => {
    render(<ProjectDetails p={project} agentName="Lodha Realty" />)

    expect(screen.getByRole('heading', { name: /project resources/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /download brochure/i })).toHaveAttribute('href', 'https://example.com/brochure.pdf')
    expect(screen.getByRole('link', { name: /emi calculator/i })).toHaveAttribute('href', 'https://example.com/emi')
    expect(screen.getByRole('heading', { name: /videos/i })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /virtual tour/i }).length).toBeGreaterThan(0)
  })
})
