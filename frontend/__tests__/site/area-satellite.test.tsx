import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import AreaMapView, { type Shown } from '@/components/site/AreaMapView'
import AreaFromAbove from '@/components/site/AreaFromAbove'
import StreetViewOnTap from '@/components/site/StreetViewOnTap'
import { boxCentre, zoomToFit } from '@/components/site/mapsEmbed'
import { AREA_CENTRES } from '@/lib/site/areaCentres'
import type { AreaMapData } from '@/lib/site/hubs'

const item = (n: number, name: string): Shown => ({
  n, slug: name.toLowerCase().replace(/[^a-z0-9]+/g, '-'), name, builder: 'Some Builder', regnos: ['P' + n], lat: 18.56, lon: 73.96,
  x: 0.2 * n, y: 0.3, stage: 'early', stage_label: 'Being built', booked: 50, total: 200, completion: '2030-07-31', price_from: null,
  photo: null, href: '/projects/' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-'), listed: false,
})
const ITEMS = [item(1, 'Godrej Ivara'), item(2, 'Lodha Camelot'), item(3, 'Yashwin Enchante')]
const DATA: AreaMapData = { area: 'upper_kharadi', area_slug: 'upper-kharadi', name: 'Upper Kharadi', map: '/maps/upper-kharadi.svg',
  box: [18.532, 73.939, 18.588, 73.998], attribution: 'Map data © OpenStreetMap contributors', items: ITEMS, left_out: 0 }

let fetchMock: jest.Mock
beforeEach(() => {
  fetchMock = jest.fn(() => Promise.resolve({ ok: true }))
  ;(global as unknown as { fetch: unknown }).fetch = fetchMock
})
afterEach(() => { delete process.env.NEXT_PUBLIC_MAPS_EMBED_KEY })

describe('the area map without the embed key', () => {
  test('renders exactly as before: no switch, no satellite frame, the drawn map and its legend shown', () => {
    const { container } = render(<AreaMapView data={DATA} items={ITEMS} />)
    expect(screen.queryByTestId('map-type-switch')).toBeNull()
    expect(screen.queryByTestId('area-satellite-frame')).toBeNull()
    expect(container.querySelector('img[src="/maps/upper-kharadi.svg"]')!.parentElement).not.toHaveClass('hidden')
    expect(screen.getByRole('list', { name: 'What the pins show' })).not.toHaveClass('hidden')
  })
})

describe('the area map with the embed key', () => {
  beforeEach(() => { process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key' })

  test('shows Map (pressed) and Satellite, and makes no Google frame before a tap', () => {
    render(<AreaMapView data={DATA} items={ITEMS} />)
    expect(screen.getByRole('button', { name: 'Map' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Satellite' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.queryByTestId('area-satellite-frame')).toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  test('a tap on Satellite opens Google at the middle of the map box, says how old it can be and tracks the area', () => {
    const { container } = render(<AreaMapView data={DATA} items={ITEMS} />)
    fireEvent.click(screen.getByRole('button', { name: 'Satellite' }))
    const src = (screen.getByTestId('area-satellite-frame') as HTMLIFrameElement).src
    expect(src).toContain('https://www.google.com/maps/embed/v1/view?key=test-key')
    expect(src).toContain('center=18.56,73.9685')
    expect(src).toContain('maptype=satellite')
    expect(src).toContain('zoom=13')
    expect(screen.getByTestId('area-satellite-note').textContent).toBe('Google’s satellite picture of Upper Kharadi. It can be months or years old.')
    expect(container.querySelector('img[src="/maps/upper-kharadi.svg"]')!.parentElement).toHaveClass('hidden')
    // the project list beside the map stays: it is the content
    expect(screen.getByTestId('area-map-list')).toBeInTheDocument()
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ feature: 'satellite_open', area: 'upper-kharadi' })
  })

  test('back to Map hides the frame without throwing it away', () => {
    render(<AreaMapView data={DATA} items={ITEMS} />)
    fireEvent.click(screen.getByRole('button', { name: 'Satellite' }))
    fireEvent.click(screen.getByRole('button', { name: 'Map' }))
    expect(screen.getByTestId('area-satellite-frame')).toHaveClass('hidden')
    expect(screen.queryByTestId('area-satellite-note')).toBeNull()
  })
})

describe('box centre and zoom', () => {
  test('the zoom fits the whole box across the drawn map, about 14 for an area 5 to 6 km wide', () => {
    expect(boxCentre([18.5265, 73.922, 18.5755, 73.974])).toEqual({ lat: 18.551, lon: 73.948 })
    expect(zoomToFit([18.5265, 73.922, 18.5755, 73.974])).toBe(14)   // Kharadi, 5.5 km
    expect(zoomToFit([18.532, 73.939, 18.588, 73.998])).toBe(13)     // Upper Kharadi, 6.2 km
    expect(zoomToFit([18.5, 73.9, 18.5, 73.9])).toBe(14)             // an empty box falls back
  })
})

describe('<area> from above, for guides without a drawn map', () => {
  test('nothing without the key', () => {
    const { container } = render(<AreaFromAbove slug="baner" name="Baner" />)
    expect(container.innerHTML).toBe('')
  })

  test('nothing for an area without a hand-set centre', () => {
    process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key'
    const { container } = render(<AreaFromAbove slug="upper-kharadi" name="Upper Kharadi" />)
    expect(container.innerHTML).toBe('')
  })

  test('with the key: a closed button, and the frame at the area centre only after the tap', () => {
    process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key'
    render(<AreaFromAbove slug="baner" name="Baner" />)
    expect(screen.getByRole('heading', { name: 'Baner from above' })).toBeInTheDocument()
    const button = screen.getByRole('button', { name: 'Show the satellite view' })
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByTestId('area-satellite-frame')).toBeNull()
    fireEvent.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'true')
    const src = (screen.getByTestId('area-satellite-frame') as HTMLIFrameElement).src
    expect(src).toContain(`center=${AREA_CENTRES.baner.lat},${AREA_CENTRES.baner.lon}`)
    expect(src).toContain('maptype=satellite')
    expect(screen.getByText('Google’s satellite picture of Baner. It can be months or years old.')).toBeInTheDocument()
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ feature: 'satellite_open', area: 'baner' })
  })

  test('every guide without a drawn map has a centre inside Pune, and says how it was chosen', () => {
    for (const slug of ['lohegaon', 'keshav-nagar', 'hinjawadi', 'wakad', 'baner']) {
      const c = AREA_CENTRES[slug]
      expect(c).toBeDefined()
      expect(c.lat).toBeGreaterThan(18.4); expect(c.lat).toBeLessThan(18.7)
      expect(c.lon).toBeGreaterThan(73.7); expect(c.lon).toBeLessThan(74.1)
      expect(c.how.length).toBeGreaterThan(10)
    }
  })
})

describe('Street View on tap', () => {
  const PLACE = { lat: 18.5515, lon: 73.9348, label: 'EON IT Park', heading: 120 }

  test('renders nothing without the key', () => {
    const { container } = render(<StreetViewOnTap {...PLACE} />)
    expect(container.innerHTML).toBe('')
  })

  test('with the key: a Street View button and no frame until it is tapped', () => {
    process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key'
    render(<StreetViewOnTap {...PLACE} />)
    const button = screen.getByRole('button', { name: /Street View/ })
    expect(button).toHaveTextContent('Street View')
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(button.className).toContain('min-h-[44px]')
    expect(screen.queryByTestId('street-view-frame')).toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  test('a tap opens Google Street View at the spot with its heading, and the caption', () => {
    process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key'
    render(<StreetViewOnTap {...PLACE} />)
    fireEvent.click(screen.getByRole('button', { name: /Street View/ }))
    const frame = screen.getByTestId('street-view-frame') as HTMLIFrameElement
    expect(frame.src).toBe('https://www.google.com/maps/embed/v1/streetview?key=test-key&location=18.5515,73.9348&heading=120&fov=90')
    expect(frame.title).toBe('Street View of EON IT Park')
    expect(screen.getByRole('button', { name: /Street View/ })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Google Street View. Pictures can be years old.')).toBeInTheDocument()
  })

  test('without a heading the URL leaves it out', () => {
    process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key'
    render(<StreetViewOnTap lat={18.5} lon={73.9} label="Somewhere" />)
    fireEvent.click(screen.getByRole('button', { name: /Street View/ }))
    expect((screen.getByTestId('street-view-frame') as HTMLIFrameElement).src)
      .toBe('https://www.google.com/maps/embed/v1/streetview?key=test-key&location=18.5,73.9&fov=90')
  })

  test('a second tap closes it but keeps the frame, so a third does not load it again', () => {
    process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key'
    render(<StreetViewOnTap {...PLACE} />)
    const button = screen.getByRole('button', { name: /Street View/ })
    fireEvent.click(button)
    fireEvent.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByTestId('street-view-frame')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
