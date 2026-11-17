import React from 'react'
import { render, screen, within } from '@testing-library/react'
import AreaLandmarks, { cleanAreaLandmarks, landmarksJsonLd } from '@/components/localities/AreaLandmarks'
import AreaMapView, { type Shown } from '@/components/site/AreaMapView'
import { mapLandmarks, type AreaMapData } from '@/lib/site/hubs'

const maps = (lat: number, lon: number) => `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`
const at = (name: string, lat: number, lon: number, km: number, distance: string, extra: Record<string, unknown> = {}) =>
  ({ name, lat, lon, km, distance, maps: maps(lat, lon), source: 'OpenStreetMap', ...extra })

// the backend's answer for Baner on 2026-11-17 (areastats/landmarks.public), shortened
const RAW = {
  area: { key: 'baner', name: 'Baner', slug: 'baner' },
  middle: { lat: 18.558994, lon: 73.784523, how: "OpenStreetMap's point for Baner", label: 'the middle of Baner' },
  metro: [
    at('Baner Gaon', 18.559196, 73.790598, 0.6, 'about 0.6 km from the middle of Baner', { kind: 'metro', line: '3',
      line_name: 'Line 3 (Pink Line, Hinjawadi to Shivajinagar)', line_short: 'Pink Line (Line 3)', status: 'being built', running: false,
      tracker: '/news/track/pune-metro-line-3' }),
    at('R K Laxman Museum Balewadi', 18.574343, 73.771849, 2, 'about 2 km north-west of the middle of Baner', { kind: 'metro', line: '3',
      line_name: 'Line 3', line_short: 'Pink Line (Line 3)', status: 'running', running: true, tracker: null }),
  ],
  landmarks: [
    at('Hinjawadi IT Park Phase 1', 18.591033, 73.735297, 6.5, 'about 6.5 km north-west of the middle of Baner', { kind: 'work', kind_label: 'Work' }),
    at('Balewadi High Street', 18.570719, 73.774308, 1.5, 'about 1.5 km north-west of the middle of Baner', { kind: 'shopping', kind_label: 'Shopping' }),
    at('Westend Mall, Aundh', 18.561655, 73.806819, 2.5, 'about 2.5 km east of the middle of Baner', { kind: 'shopping', kind_label: 'Shopping' }),
    at('Jupiter Hospital, Baner', 18.565745, 73.785996, 0.8, 'about 0.8 km from the middle of Baner', { kind: 'hospital', kind_label: 'Hospitals' }),
    at('Pune Junction railway station', 18.528877, 73.874415, 10, 'about 10 km east of the middle of Baner', { kind: 'travel', kind_label: 'Travel' }),
  ],
  note: 'Straight-line distances from the middle of Baner, rounded; not travel times.',
  attribution: 'Positions © OpenStreetMap contributors',
}

describe('landmarks near an area', () => {
  it('groups the places by kind, each name opening Google Maps in a new tab', () => {
    render(<AreaLandmarks data={cleanAreaLandmarks(RAW, 'baner')} />)
    const s = screen.getByTestId('area-landmarks')
    expect(within(s).getByRole('heading', { level: 2 }).textContent).toBe('Landmarks near Baner')
    expect(within(s).getAllByRole('heading', { level: 3 }).map((h) => h.textContent)).toEqual(['Metro', 'Work', 'Shopping', 'Hospitals', 'Travel'])
    const mall = within(s).getByRole('link', { name: 'Westend Mall, Aundh (opens in a new tab)' })
    expect(mall).toHaveAttribute('href', maps(18.561655, 73.806819))
    expect(mall).toHaveAttribute('target', '_blank')
    expect(mall.getAttribute('rel')).toContain('noopener')
    expect(s.textContent).toContain('about 2.5 km east of the middle of Baner')
    expect(s.textContent).toContain('not travel times')
  })

  it('says the metro line and status in words, and a station being built links its tracker', () => {
    render(<AreaLandmarks data={cleanAreaLandmarks(RAW, 'baner')} />)
    const items = screen.getAllByRole('listitem').filter((li) => /station/.test(li.textContent || ''))
    expect(items[0].textContent).toContain('Baner Gaon station')
    expect(items[0].textContent).toContain('Pink Line (Line 3), being built, not open yet')
    expect(within(items[0]).getByRole('link', { name: 'Follow its progress' })).toHaveAttribute('href', '/news/track/pune-metro-line-3')
    expect(items[1].textContent).toContain('Pink Line (Line 3), running')
    expect(within(items[1]).queryByRole('link', { name: 'Follow its progress' })).toBeNull()
  })

  it('never says a station is running unless the answer says so in both fields', () => {
    const odd = { ...RAW, metro: [{ ...RAW.metro[0], status: 'running', running: false }] }
    const got = cleanAreaLandmarks(odd, 'baner')!
    expect(got.metro[0].status).toBe('being built')
    expect(got.metro[0].running).toBe(false)
  })

  it('adds the places with their positions to the page data', () => {
    const ld = landmarksJsonLd(cleanAreaLandmarks(RAW, 'baner')!) as { itemListElement: { item: Record<string, unknown> }[] }
    const items = ld.itemListElement.map((e) => e.item)
    expect(items[0]).toMatchObject({ '@type': 'TrainStation', name: 'Baner Gaon metro station' })
    expect(items.find((i) => i.name === 'Jupiter Hospital, Baner')).toMatchObject({ '@type': 'Hospital',
      geo: { '@type': 'GeoCoordinates', latitude: 18.565745, longitude: 73.785996 } })
  })

  it('renders nothing on a failed read, another area, an empty answer or a malformed one', () => {
    const { container } = render(<AreaLandmarks data={null} />)
    expect(container.innerHTML).toBe('')
    expect(cleanAreaLandmarks(RAW, 'wakad')).toBeNull()
    expect(cleanAreaLandmarks({ ...RAW, metro: [], landmarks: [] }, 'baner')).toBeNull()
    expect(cleanAreaLandmarks('oops', 'baner')).toBeNull()
    // a link that is not Google Maps' is dropped, not shown
    const bad = cleanAreaLandmarks({ ...RAW, metro: [], landmarks: [{ ...RAW.landmarks[0], maps: 'https://evil.example/' }] }, 'baner')
    expect(bad).toBeNull()
  })
})

describe('landmarks on the area map', () => {
  const item: Shown = { n: 1, slug: 'godrej-ivara', name: 'Godrej Ivara', builder: null, regnos: ['P1'], lat: 18.55, lon: 73.96, x: 0.5,
    y: 0.6, stage: 'new', stage_label: 'New launch', booked: null, total: null, completion: null, price_from: null, photo: null,
    href: '/projects/godrej-ivara', listed: false }
  const DATA: AreaMapData = { area: 'kharadi', area_slug: 'kharadi', name: 'Kharadi', map: '/maps/kharadi.svg', box: [18.5265, 73.922, 18.5755, 73.974],
    attribution: 'Map data © OpenStreetMap contributors', items: [item], left_out: 0,
    landmarks: mapLandmarks([
      { name: 'EON IT Park (EON Free Zone)', icon: 'office', x: 0.25, y: 0.5, lat: 18.55, lon: 73.95, label: 'EON IT Park (EON Free Zone)' },
      { name: 'Manipal Hospital, Kharadi', icon: 'hospital', x: 0.26, y: 0.71, lat: 18.54, lon: 73.93, label: 'Manipal Hospital, Kharadi' },
      { name: 'Somewhere', icon: 'castle', x: 0.5, y: 0.5, lat: 18.5, lon: 73.9, label: 'Somewhere' },     // a kind the map cannot draw
      { name: 'Far away', icon: 'metro', x: 1.4, y: 0.5, lat: 18.5, lon: 73.9, label: 'Far away metro (running)' },  // outside the frame
    ]) }

  it('draws only drawable icons inside the frame, apart from the numbered pins, and names them under the map', () => {
    render(<AreaMapView data={DATA} items={[item]} />)
    const icons = screen.getAllByTestId('area-map-landmark')
    expect(icons.map((i) => i.getAttribute('title'))).toEqual(['EON IT Park (EON Free Zone)', 'Manipal Hospital, Kharadi'])
    expect(icons[0].getAttribute('style')).toContain('left: 25%')
    expect(screen.getAllByTestId('area-map-pin')).toHaveLength(1)          // icons are not pins: nothing to press
    const legend = screen.getByTestId('area-map-landmark-legend')
    expect(legend.textContent).toContain('EON IT Park (EON Free Zone) (office hub)')
    expect(legend.textContent).toContain('Manipal Hospital, Kharadi (hospital)')
  })

  it('a map answer without landmarks draws none and says nothing about them', () => {
    render(<AreaMapView data={{ ...DATA, landmarks: undefined }} items={[item]} />)
    expect(screen.queryAllByTestId('area-map-landmark')).toHaveLength(0)
    expect(screen.queryByTestId('area-map-landmark-legend')).toBeNull()
  })
})
