import React from 'react'
import { fireEvent, render, screen, within } from '@testing-library/react'
import AreaMapView, { pct, placeLabels, type Shown } from '@/components/site/AreaMapView'
import type { AreaMapData } from '@/lib/site/hubs'

const item = (n: number, name: string, x: number, y: number, extra: Partial<Shown> = {}): Shown => ({
  n, slug: name.toLowerCase().replace(/[^a-z0-9]+/g, '-'), name, builder: 'Some Builder', regnos: ['P' + n], lat: 18.56, lon: 73.96, x, y,
  stage: 'early', stage_label: 'Being built', booked: 50, total: 200, completion: '2030-07-31', price_from: 12900000, photo: null,
  href: '/projects/' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-'), listed: false, ...extra,
})

const ITEMS = [
  item(1, 'Godrej Ivara', 0.5, 0.6, { stage: 'new', stage_label: 'New launch', booked: 489, total: 2792 }),
  item(2, 'Lodha Camelot', 0.3, 0.3, { href: '/projects/lodha-camelot', listed: true }),
  item(3, 'Yashwin Enchante', 0.7, 0.2, { stage: 'advanced', stage_label: 'Nearly ready', booked: 887, total: 941, price_from: null }),
]
const DATA: AreaMapData = { area: 'upper_kharadi', area_slug: 'upper-kharadi', name: 'Upper Kharadi', map: '/maps/upper-kharadi.svg',
  box: [18.532, 73.939, 18.588, 73.998], attribution: 'Map data © OpenStreetMap contributors', items: ITEMS, left_out: 2 }

describe('area map', () => {
  it('labels a pin where its name fits and keeps only the number for pins in a cluster', () => {
    const got = placeLabels([
      { n: 1, name: 'Lodha Camelot', x: 0.5, y: 0.5 },
      { n: 2, name: 'Lodha Giardino', x: 0.53, y: 0.5 },     // next door: the two names go on opposite sides
      { n: 3, name: 'Pristine O2 World', x: 0.515, y: 0.51 }, // between them: no room, the list says its name
      { n: 4, name: 'Yashwin Enchante', x: 0.95, y: 0.2 },    // at the right edge: its label goes left
    ])
    expect(got).toEqual({ 1: 'left', 2: 'right', 4: 'left' })
  })

  it('reads in full without JavaScript: every project a link, the first one picked, the map credited', () => {
    render(<AreaMapView data={DATA} items={ITEMS} />)
    const list = screen.getByTestId('area-map-list')
    expect(within(list).getAllByRole('link').map((a) => a.getAttribute('href')))
      .toEqual(['/projects/godrej-ivara', '/projects/lodha-camelot', '/projects/yashwin-enchante'])
    const card = screen.getByTestId('area-map-card')
    expect(card.textContent).toContain('1. Godrej Ivara')
    expect(card.textContent).toContain('₹1.29 Cr')
    expect(card.textContent).toContain('Jul 2030')
    expect(card.textContent).toContain('489 of 2,792 homes booked on MahaRERA')
    expect(within(card).getByRole('link', { name: 'Directions in Google Maps' }).getAttribute('href')).toContain('query=18.56,73.96')
    expect(screen.getByText('Map data © OpenStreetMap contributors')).toBeInTheDocument()
    expect(screen.getAllByTestId('area-map-pin')[0]).toHaveAttribute('aria-label', '1. Godrej Ivara, 18% booked')
  })

  it('picking a pin shows that project, and an agent-listed one links its own page', () => {
    render(<AreaMapView data={DATA} items={ITEMS} />)
    fireEvent.click(screen.getByRole('button', { name: /^2\. Lodha Camelot/ }))
    const card = screen.getByTestId('area-map-card')
    expect(card.textContent).toContain('2. Lodha Camelot')
    expect(within(card).getByRole('link', { name: 'See Lodha Camelot' })).toHaveAttribute('href', '/projects/lodha-camelot')
    fireEvent.click(screen.getByRole('button', { name: /^3\. Yashwin/ }))
    expect(screen.getByTestId('area-map-card').textContent).toContain('FromAsk')   // no published price: never a guess
  })

  it('booked share is only shown when MahaRERA gives both numbers', () => {
    expect(pct({ booked: 887, total: 941 })).toBe(94)
    expect(pct({ booked: null, total: 941 })).toBeNull()
    expect(pct({ booked: 3, total: 0 })).toBeNull()
  })
})
