import React from 'react'
import { render, screen } from '@testing-library/react'
import EsriPastPictures from '@/components/site/EsriPastPictures'
import ProjectFromAbove from '@/components/site/ProjectFromAbove'
import { esriPastFrom, metresAcross, tileOf } from '@/lib/site/esriPast'
import { fromRecord } from '@/lib/site/fromAbove'

const PIN = { lat: 18.5447756, lon: 73.9685329 }
const raw = { zoom: 17, shots: [
  { release: 39767, captured: '2022-11-12', source: 'Maxar', res: 0.31 },
  { release: 27982, captured: '2024-01-11', source: 'Maxar', res: 0.31 },
  { release: 64001, captured: '2025-02-02', source: 'Vantor', res: 0.31 },
  { release: 3692, captured: '2026-04-04', source: 'Vantor', res: 0.34 },
] }

describe("Esri's sharp past pictures", () => {
  it('keeps only real releases and dates, oldest first, and needs two', () => {
    const got = esriPastFrom({ ...raw, shots: [...raw.shots].reverse().concat([{ release: -1, captured: '2020-01-01', source: '', res: 1 },
      { release: 5, captured: 'yesterday', source: '', res: 1 }] as never) })
    expect(got?.shots.map((s) => s.captured)).toEqual(['2022-11-12', '2024-01-11', '2025-02-02', '2026-04-04'])
    expect(esriPastFrom({ ...raw, shots: raw.shots.slice(0, 1) })).toBeNull()
    expect(esriPastFrom({ ...raw, zoom: 25 })).toBeNull()
    expect(esriPastFrom(null)).toBeNull()
  })

  it("finds the pin in Esri's tile grid as its own tile service numbers it", () => {
    const t = tileOf(PIN.lat, PIN.lon, 18)
    expect([t.col, t.row]).toEqual([184934, 117325])      // the tile Esri served for Kohinoor Riverdale's pin, 2026-11-21
    expect(Math.round(metresAcross(PIN.lat, 17))).toBe(580)            // the Sentinel frame's 600 m, near enough
    expect(Math.round(metresAcross(PIN.lat, 18))).toBe(290)
  })

  it('shows each dated picture from Esri, centred on the pin with the ring, the dates said in the text', () => {
    render(<EsriPastPictures past={esriPastFrom(raw)!} lat={PIN.lat} lon={PIN.lon} name="Kohinoor Riverdale" centredOn="the project's map pin" ringM={100} />)
    expect(screen.getByText(/Sharp satellite pictures taken in Nov 2022, Jan 2024, Feb 2025 and Apr 2026, centred on the project's map pin/)).toBeTruthy()
    expect(screen.getAllByTestId('esri-past-picture')).toHaveLength(4)
    const middle = screen.getByAltText('Kohinoor Riverdale from above, satellite picture of Apr 2026') as HTMLImageElement
    expect(middle.getAttribute('src')).toBe('https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/3692/17/58662/92467')
    expect(middle.getAttribute('loading')).toBe('lazy')
    expect(screen.getByText(/Esri World Imagery · Maxar, Vantor/)).toBeTruthy()
    expect(screen.getByRole('link', { name: /Compare every release/ }).getAttribute('href')).toContain('mapCenter=73.968533%2C18.544776%2C17')
  })

  it("takes the framed Wayback viewer's place in the project section", () => {
    const DIR = '/uploads/from_above/p1'
    const frame = (year: number) => ({ year, day: `${year}-02-15`, src: `${DIR}/${year}.webp`, width: 600, height: 600 })
    const view = fromRecord({ pin: PIN, story: 'The ground around the pin.', where: 'w', credit: 'c',
      frames: [frame(2022), frame(2024), frame(2026)], seasons: [], video: null }, 'p1')!
    const { rerender } = render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" esriPast={esriPastFrom(raw)} />)
    expect(screen.getByTestId('esri-past')).toBeTruthy()
    expect(screen.queryByTestId('esri-wayback')).toBeNull()
    rerender(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    expect(screen.getByTestId('esri-wayback')).toBeTruthy()      // until the pictures are looked up
  })
})
