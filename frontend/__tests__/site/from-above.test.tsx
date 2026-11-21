import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import ProjectFromAbove from '@/components/site/ProjectFromAbove'
import { waybackSrc } from '@/components/site/EsriWaybackOnTap'
import { forPin, fromRecord } from '@/lib/site/fromAbove'

const SLUG = 'kohinoor-riverdale-kharadi'
const DIR = '/uploads/from_above/p52100056021'
const frame = (year: number) => ({ year, day: `${year}-02-27`, src: `${DIR}/${year}.webp`, width: 600, height: 600 })
const STORY = 'The ground around the project’s map pin, seen by the Sentinel-2 satellite once each dry season from Jan 2021 to Nov 2026.'
const video = { src: `${DIR}/months.mp4`, poster: `${DIR}/months.webp`, width: 720, height: 720, from: '2021-01-20', to: '2026-11-11', months: 17 }
const raw = {
  pin: { lat: 18.5447756, lon: 73.9685329 }, story: STORY,
  where: 'The yellow ring marks the project’s map pin. Each picture is 600 m across at 10 m a pixel: it takes in neighbouring plots, and shows ground, not floors.',
  credit: 'Contains modified Copernicus Sentinel data 2021-2026',
  frames: [frame(2021), frame(2022), frame(2023), frame(2026)], video, updated: '2026-11-20', registered: '2022-08-10',
  seasons: [{ label: 'Jan-Mar 2021', day: '2021-01-01', line: 'Open ground with a track; nothing built in the ring.' },
    ...Array.from({ length: 7 }, (_, i) => ({ label: `Oct-Dec ${2021 + i}`, day: `${2021 + i}-10-01`, line: `Line ${i}.` }))],
}

describe('the site from above', () => {
  it('keeps only pictures stored for this project, with their year in the name', () => {
    const bad = { ...raw, frames: [...raw.frames, { ...frame(2024), src: '/uploads/elsewhere/2024.webp' },
      { ...frame(2025), src: `/uploads/from_above/x/../../2025.webp` }] }
    expect(fromRecord(bad, SLUG)?.frames.map((f) => f.year)).toEqual([2021, 2022, 2023, 2026])
  })

  it('shows nothing without a sentence, with fewer than three years, or for nothing at all', () => {
    expect(fromRecord({ ...raw, story: '' }, SLUG)).toBeNull()
    expect(fromRecord({ ...raw, frames: raw.frames.slice(0, 2) }, SLUG)).toBeNull()
    expect(fromRecord(null, SLUG)).toBeNull()
  })

  it('shows nothing once the checked pin has moved away from where the pictures were taken', () => {
    const view = fromRecord(raw, SLUG)
    expect(forPin(view, { lat: 18.5448, lon: 73.9686 })).not.toBeNull()   // a few metres
    expect(forPin(view, { lat: 18.5457, lon: 73.9685 })).toBeNull()       // about 100 m north
    expect(forPin(view, null)).toBeNull()
  })

  const open = () => {
    const proof = screen.getByTestId('from-above-proof') as HTMLDetailsElement
    proof.open = true
    fireEvent(proof, new Event('toggle'))
  }

  it('renders each year by its month once the proof is opened, and never a share of roofs or concrete', () => {
    const view = fromRecord(raw, SLUG)!
    const { container } = render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    expect(screen.getByRole('heading', { name: 'Kohinoor Riverdale from above, today' })).toBeTruthy()
    expect(screen.getByText(STORY)).toBeTruthy()
    open()
    expect(screen.getAllByRole('img')).toHaveLength(4)
    expect(container.textContent).not.toMatch(/%/)
    const small = screen.getByText(/neighbouring plots/)
    expect(small.textContent).toContain('nothing is drawn in')
    expect(small.textContent).toContain('Copernicus Sentinel data')
  })

  it('keeps the Sentinel pictures and video out of the page until the reader opens the proof badge', () => {
    render(<ProjectFromAbove view={fromRecord(raw, SLUG)!} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    expect(screen.getByTestId('from-above-proof').textContent).toContain('Construction proof from space: Jan 2021 to Nov 2026, Copernicus Sentinel-2')
    expect(screen.queryAllByRole('img')).toHaveLength(0)
    expect(screen.queryByTestId('from-above-video')).toBeNull()
    open()
    expect(screen.getByTestId('from-above-video')).toBeTruthy()
  })

  it('plays the season-by-season video once, only when its files are the project’s own, and names it for search', () => {
    expect(fromRecord({ ...raw, video: { ...video, poster: '/uploads/other.webp' } }, SLUG)?.video).toBeNull()
    expect(fromRecord({ ...raw, video: { ...video, months: 2 } }, SLUG)?.video).toBeNull()
    const view = fromRecord(raw, SLUG)!
    const { container } = render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    const ld = JSON.parse(container.querySelector('script[type="application/ld+json"]')!.innerHTML)
    const vo = ld['@graph'].find((g: { '@type': string }) => g['@type'] === 'VideoObject')
    expect(vo.contentUrl).toBe(`https://avasetu.in${DIR}/months.mp4`)   // named for search with the badge closed
    expect(vo.name).toBe('Kohinoor Riverdale from space, Jan 2021 to Nov 2026')
    expect(vo.transcript).toContain('Jan-Mar 2021: Open ground with a track')
    expect(vo.uploadDate).toBe('2026-11-20')
    open()
    const el = screen.getByTestId('from-above-video') as HTMLVideoElement
    expect(el.getAttribute('poster')).toBe(video.poster)
    expect(el.muted).toBe(true)
    expect(el.loop).toBe(false)
    expect(el.controls).toBe(true)
    expect(el.getAttribute('src')).toBeNull()            // nothing downloads before it is near the screen
    expect(screen.getByText(/17 clear months, October to May/)).toBeTruthy()
  })

  it('gives the newest season as the latest reading, with the registration and the filed possession', () => {
    render(<ProjectFromAbove view={fromRecord(raw, SLUG)!} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" possession="Dec 2028" />)
    const latest = screen.getByTestId('from-above-latest')
    expect(latest.textContent).toContain('Latest reading from space, Oct–Dec 2027 (looked Nov 2026)')
    expect(latest.textContent).toContain('Line 6.')
    expect(screen.getByTestId('from-above-dates').textContent).toBe('Registered with MahaRERA Aug 2022 · possession filed for Dec 2028')
    expect(fromRecord({ ...raw, registered: 'soon' }, SLUG)!.registered).toBeNull()
  })

  it('keeps every season line in the page: the three before the latest shown, the earlier ones in the proof badge', () => {
    const view = fromRecord(raw, SLUG)!
    render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    const box = screen.getByTestId('from-above-seasons')
    expect(box.textContent).toContain('Line 5.')
    expect(box.textContent).not.toContain('Line 6.')                  // the latest reading, above
    expect(screen.getByTestId('from-above-earlier').textContent).toContain('Open ground with a track')   // folded, still in the page
    expect(fromRecord({ ...raw, seasons: [{ label: 'x', day: 'nope', line: 'y' }] }, SLUG)!.seasons).toEqual([])
  })

  it('opens with Google’s live satellite view, the latest reading under it and the Sentinel proof after', () => {
    const before = process.env.NEXT_PUBLIC_MAPS_EMBED_KEY
    process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = 'test-key'
    try {
      render(<ProjectFromAbove view={fromRecord(raw, SLUG)!} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
      const today = screen.getByTestId('from-above-today')
      const latest = screen.getByTestId('from-above-latest')
      const proof = screen.getByTestId('from-above-proof')
      expect(today.compareDocumentPosition(latest) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
      expect(latest.compareDocumentPosition(proof) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
      expect(today.querySelector('iframe')!.getAttribute('src')).toContain('maptype=satellite')
    } finally {
      process.env.NEXT_PUBLIC_MAPS_EMBED_KEY = before
    }
  })

  it('offers Esri’s sharp past pictures at the pin, asking Esri for nothing until the reader taps', () => {
    render(<ProjectFromAbove view={fromRecord(raw, SLUG)!} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    expect(screen.queryByTestId('esri-wayback-frame')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Compare sharp past pictures' }))
    const frame = screen.getByTestId('esri-wayback-frame')
    expect(frame.getAttribute('src')).toBe('https://livingatlas.arcgis.com/wayback/#mapCenter=73.968533%2C18.544776%2C17&mode=swipe')
    expect(waybackSrc(18.5, 73.9, 16)).toContain('mapCenter=73.900000%2C18.500000%2C16')   // longitude first, as Esri reads it
    expect(screen.getByText(/Not every release has a new picture of this/)).toBeTruthy()
  })
})
