import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import LocationMapSwitch from '@/components/site/LocationMapSwitch'

const PROPS = { lat: 18.5553, lon: 73.9375, shown: 'Lodha Giardino', osmSrc: 'https://www.openstreetmap.org/export/embed.html?bbox=73.9275,18.5453,73.9475,18.5653&layer=mapnik&marker=18.5553,73.9375', osmLink: 'https://www.openstreetmap.org/?mlat=18.5553&mlon=73.9375#map=15/18.5553/73.9375' }

describe('no Maps Embed key', () => {
  beforeEach(() => { delete process.env.NEXT_PUBLIC_MAPS_EMBED_KEY })

  test('renders the OSM iframe with no tab switch', () => {
    render(<LocationMapSwitch {...PROPS} />)
    expect(screen.queryByTestId('map-type-switch')).toBeNull()
    expect(screen.getByTitle('Map around Lodha Giardino')).toBeInTheDocument()
  })

  test('no satellite frame is in the DOM', () => {
    render(<LocationMapSwitch {...PROPS} />)
    expect(screen.queryByTestId('satellite-frame')).toBeNull()
  })
})

describe('with Maps Embed key', () => {
  beforeEach(() => { process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key' })
  afterEach(() => { delete process.env.NEXT_PUBLIC_MAPS_EMBED_KEY })

  test('Map and Satellite tabs are shown', () => {
    render(<LocationMapSwitch {...PROPS} />)
    expect(screen.getByRole('button', { name: 'Map' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Satellite' })).toBeInTheDocument()
  })

  test('Map tab is pressed by default; OSM iframe visible; no satellite frame yet', () => {
    render(<LocationMapSwitch {...PROPS} />)
    expect(screen.getByRole('button', { name: 'Map' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Satellite' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByTitle('Map around Lodha Giardino')).not.toHaveClass('hidden')
    expect(screen.queryByTestId('satellite-frame')).toBeNull()
  })

  test('tapping Satellite creates the satellite iframe with the right src', () => {
    render(<LocationMapSwitch {...PROPS} />)
    fireEvent.click(screen.getByRole('button', { name: 'Satellite' }))
    const frame = screen.getByTestId('satellite-frame') as HTMLIFrameElement
    expect(frame.src).toContain('key=test-key')
    expect(frame.src).toContain(`center=${PROPS.lat},${PROPS.lon}`)
    expect(frame.src).toContain('maptype=satellite')
  })

  test('tapping Satellite hides the OSM iframe and shows the age note', () => {
    render(<LocationMapSwitch {...PROPS} />)
    fireEvent.click(screen.getByRole('button', { name: 'Satellite' }))
    expect(screen.getByTitle('Map around Lodha Giardino')).toHaveClass('hidden')
    expect(screen.getByTestId('satellite-note')).toBeInTheDocument()
  })

  test('tapping Map again hides the satellite iframe and removes the note', () => {
    render(<LocationMapSwitch {...PROPS} />)
    fireEvent.click(screen.getByRole('button', { name: 'Satellite' }))
    fireEvent.click(screen.getByRole('button', { name: 'Map' }))
    expect(screen.getByTestId('satellite-frame')).toHaveClass('hidden')
    expect(screen.queryByTestId('satellite-note')).toBeNull()
    expect(screen.getByTitle('Map around Lodha Giardino')).not.toHaveClass('hidden')
  })

  test('switching back to Map does not destroy and re-create the satellite iframe (lazy stays loaded)', () => {
    render(<LocationMapSwitch {...PROPS} />)
    fireEvent.click(screen.getByRole('button', { name: 'Satellite' }))
    fireEvent.click(screen.getByRole('button', { name: 'Map' }))
    // satellite frame is still in the DOM (just hidden), so a second switch back does not re-fetch
    expect(screen.queryByTestId('satellite-frame')).toBeInTheDocument()
  })
})
