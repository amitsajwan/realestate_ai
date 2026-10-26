import { render, screen } from '@testing-library/react'
import React from 'react'
import BuilderDateMoves from '@/components/site/BuilderDateMoves'

// A builder's date changes as we saw them file each one (docs/plan/seo-system.md 8b, H3)
describe("a builder's date changes", () => {
  it('lists each change with its project link, the two dates and the day we saw it', () => {
    render(<BuilderDateMoves b={{ name: 'Rohan Builders', date_moves: [
      { slug: 'two', name: 'Rohan Two', seen_on: '2026-10-10', from: '2030-03-31', to: '2030-12-31' },
      { slug: 'one', name: 'Rohan One', seen_on: null, from: '2028-12-31', to: '2029-06-30' }] }} />)
    const list = screen.getByTestId('date-moves')
    expect(list).toHaveTextContent('Date changes we saw Rohan Builders file')
    expect(list).toHaveTextContent('Rohan Two31 Mar 2030 → 31 Dec 2030, seen 10 Oct 2026')
    expect(screen.getByRole('link', { name: 'Rohan One' })).toHaveAttribute('href', '/projects/one')
  })

  it('shows nothing when we saw no change, or the page predates the list', () => {
    const { container } = render(<BuilderDateMoves b={{ name: 'X', date_moves: [] }} />)
    expect(container).toBeEmptyDOMElement()
    expect(render(<BuilderDateMoves b={{ name: 'X' }} />).container).toBeEmptyDOMElement()
  })
})
