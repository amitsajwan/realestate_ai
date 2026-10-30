import { render, screen } from '@testing-library/react'
import React from 'react'
import FinderCard from '@/components/site/finder/FinderCard'
import type { FinderItem } from '@/lib/site/finder'

const item = (listedBy: string | null): FinderItem => ({
  id: 'p', href: '/projects/p', name: 'Godrej Ivara', builder: 'Godrej', area: 'Upper Kharadi', type: 'apartment',
  homes: [{ bhk: 2, sqft: 700, price: 12_000_000 }], possession: null, monthsLater: null, booked: null, total: null,
  video: false, image: null, map: null, rank: 0, listedBy,
})

it("names a partner agent on the card but not Avasetu's own listing", () => {
  const { unmount } = render(<FinderCard item={item('House Deal')} q={{}} basePath="/projects" />)
  expect(screen.getByText('Listed by House Deal')).toBeInTheDocument()
  unmount()
  render(<FinderCard item={item('Avasetu')} q={{}} basePath="/projects" />)
  expect(screen.queryByText(/Listed by|Through/)).not.toBeInTheDocument()
})
