import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import CardPicture from '@/components/site/CardPicture'

const pic = (n: number, source = 'builder') => ({ url: `/uploads/p/${n}.webp`, alt: `View ${n}`, source })
const LOGO = { url: '/uploads/builder_logos/lodha.png', width: 200, height: 80, tone: 'dark' as const, site: 'lodhagroup.com' }
const MAP = { url: '/uploads/location_maps/p.png', width: 960, height: 540 }
const shown = (c: HTMLElement) => c.querySelector('img.opacity-100')?.getAttribute('src')

describe("a project card's picture", () => {
  it('steps through several pictures with the arrows, round from the last to the first, and never by itself', () => {
    jest.useFakeTimers()
    const { container } = render(<CardPicture m={{ photos: [pic(1), pic(2), pic(3)] }} name="Lodha Camelot" href="/projects/x" />)
    expect(shown(container)).toBe('/uploads/p/1.webp')
    jest.advanceTimersByTime(60_000)
    expect(shown(container)).toBe('/uploads/p/1.webp')   // no autoplay: rows of cards never move by themselves
    expect(screen.getByText('1 / 3')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next picture of Lodha Camelot' }))
    expect(shown(container)).toBe('/uploads/p/2.webp')
    fireEvent.click(screen.getByRole('button', { name: 'Previous picture of Lodha Camelot' }))
    fireEvent.click(screen.getByRole('button', { name: 'Previous picture of Lodha Camelot' }))
    expect(shown(container)).toBe('/uploads/p/3.webp')
    expect(screen.getByText('3 / 3')).toBeInTheDocument()
    jest.useRealTimers()
  })

  it("has no arrows for one picture, and says when the shown one is an artist's impression", () => {
    render(<CardPicture m={{ photo: pic(1, 'brochure') }} name="P" href="/projects/x" />)
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.getByText("Artist's impression")).toBeInTheDocument()
  })

  it("with no picture shows the street map with the builder's logo over it, as the project page does", () => {
    render(<CardPicture m={{ photos: [], location_picture: MAP, logo: LOGO }} name="P" href="/projects/x" />)
    expect(screen.getByTestId('card-map')).toHaveAttribute('src', MAP.url)
    expect(screen.getByTestId('card-map-logo')).toBeInTheDocument()
    expect(screen.queryByTestId('card-logo')).toBeNull()
  })

  it("with no picture and no map shows the builder's logo, and with nothing at all the skyline", () => {
    const { unmount } = render(<CardPicture m={{ logo: LOGO }} name="P" href="/projects/x" />)
    expect(screen.getByTestId('card-logo')).toBeInTheDocument()
    unmount()
    const { container } = render(<CardPicture m={{}} name="P" href="/projects/x" />)
    expect(container.querySelector('img')).toBeNull()
    expect(container.querySelector('svg')).not.toBeNull()
  })
})
