import React from 'react'
import { render, screen } from '@testing-library/react'
import ProjectFromAbove from '@/components/site/ProjectFromAbove'
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
  frames: [frame(2021), frame(2022), frame(2023), frame(2026)], video, updated: '2026-11-20',
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

  it('renders each year by its month and never a share of roofs or concrete', () => {
    const view = fromRecord(raw, SLUG)!
    const { container } = render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    expect(screen.getByRole('heading', { name: 'Kohinoor Riverdale from space, 2021 to 2026' })).toBeTruthy()
    expect(screen.getAllByRole('img')).toHaveLength(4)
    expect(screen.getByText(STORY)).toBeTruthy()
    expect(container.textContent).not.toMatch(/%/)
    const small = screen.getByText(/neighbouring plots/)
    expect(small.textContent).toContain('nothing is drawn in')
    expect(small.textContent).toContain('Copernicus Sentinel data')
  })

  it('plays the season-by-season video once, only when its files are the project’s own, and names it for search', () => {
    expect(fromRecord({ ...raw, video: { ...video, poster: '/uploads/other.webp' } }, SLUG)?.video).toBeNull()
    expect(fromRecord({ ...raw, video: { ...video, months: 2 } }, SLUG)?.video).toBeNull()
    const view = fromRecord(raw, SLUG)!
    const { container } = render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    const el = screen.getByTestId('from-above-video') as HTMLVideoElement
    expect(el.getAttribute('poster')).toBe(video.poster)
    expect(el.muted).toBe(true)
    expect(el.loop).toBe(false)
    expect(el.controls).toBe(true)
    expect(el.getAttribute('src')).toBeNull()            // nothing downloads before it is near the screen
    expect(screen.getByText(/17 clear months, October to May/)).toBeTruthy()
    const ld = JSON.parse(container.querySelector('script[type="application/ld+json"]')!.innerHTML)
    const vo = ld['@graph'].find((g: { '@type': string }) => g['@type'] === 'VideoObject')
    expect(vo.contentUrl).toBe(`https://avasetu.in${DIR}/months.mp4`)
    expect(vo.name).toBe('Kohinoor Riverdale from space, Jan 2021 to Nov 2026')
    expect(vo.transcript).toContain('Jan-Mar 2021: Open ground with a track')
    expect(vo.uploadDate).toBe('2026-11-20')
  })

  it('shows the newest seasons as page text and folds the earlier ones away', () => {
    const view = fromRecord(raw, SLUG)!
    render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    const box = screen.getByTestId('from-above-seasons')
    expect(box.textContent).toContain('Line 6.')                    // the newest
    expect(box.querySelector('details')!.textContent).toContain('Open ground with a track')   // folded, still in the page
    expect(fromRecord({ ...raw, seasons: [{ label: 'x', day: 'nope', line: 'y' }] }, SLUG)!.seasons).toEqual([])
  })
})

