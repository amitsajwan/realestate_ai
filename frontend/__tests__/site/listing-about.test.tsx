import React from 'react'
import { render, screen, within } from '@testing-library/react'
import ListingAbout from '@/components/site/ListingAbout'

// The public listing page's "About the project" section (Studio's About step fills it; its tests are in studio/__tests__).
describe('public listing about section', () => {
  const about = {
    project_name: 'Riverfront Residences', highlights: ['East facing'], amenities: ['Lift', 'Gym'],
    nearby: [{ type: 'school', name: 'School nearby' }, { type: 'office', name: 'EON Free Zone', minutes: 10 }],
    connectivity: ['Metro Line 4 is approved, not running yet.'], water: '24x7 water supply',
  }
  it('renders highlights, amenities, facts and nearby; hides amenities already shown above', () => {
    render(<ListingAbout about={about} listingAmenities={['Gym']} />)
    const sec = screen.getByTestId('listing-about')
    expect(within(sec).getByText('About the project: Riverfront Residences')).toBeInTheDocument()
    expect(within(sec).getByText('East facing')).toBeInTheDocument()
    expect(within(sec).getByText('Lift')).toBeInTheDocument()
    expect(within(sec).queryByText('Gym')).toBeNull()
    expect(within(sec).getByText('24x7 water supply')).toBeInTheDocument()
    expect(within(sec).getByText('School nearby')).toBeInTheDocument()
    expect(within(sec).getByText(/about 10 min/)).toBeInTheDocument()
    expect(within(sec).getByText(/approved, not running/)).toBeInTheDocument()
  })
  it('renders nothing without about', () => {
    const { container, rerender } = render(<ListingAbout about={null} />)
    expect(container).toBeEmptyDOMElement()
    rerender(<ListingAbout about={{}} />)
    expect(container).toBeEmptyDOMElement()
  })
})
