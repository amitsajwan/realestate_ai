import React from 'react'
import path from 'path'
import { render, screen } from '@testing-library/react'
import ProjectFromAbove from '@/components/site/ProjectFromAbove'
import { cleanFromAbove, forPin, fromRecord, readFromAbove } from '@/lib/site/fromAbove'

const SLUG = 'kohinoor-riverdale-kharadi'
const frame = (year: number, built: number) => ({
  year, day: `${year}-02-27`, src: `/from-above/${SLUG}-${year}.webp`, width: 600, height: 600, built, bare: 10, green: 20,
})
const raw = {
  slug: SLUG, pin: { lat: 18.5447756, lon: 73.9685329 },
  story: 'Within 100 m of the map pin, by Feb 2026 roofs and concrete covered 22% of the ground, against 0% in Feb 2021.',
  where: 'Measured within 100 m of the map pin. The circle takes in neighbouring plots.',
  credit: 'Contains modified Copernicus Sentinel data 2021-2026',
  frames: [frame(2021, 0), frame(2022, 0), frame(2023, 2), frame(2026, 22)],
}

describe('the site from above', () => {
  it('keeps only frames whose file, year and numbers agree', () => {
    const bad = { ...raw, frames: [...raw.frames, { ...frame(2024, 16), src: '/from-above/other-2024.webp' }, { ...frame(2025, 150) }] }
    const view = cleanFromAbove(bad, SLUG)
    expect(view?.frames.map((f) => f.year)).toEqual([2021, 2022, 2023, 2026])
  })

  it('shows nothing for another slug, no sentence or fewer than three years', () => {
    expect(cleanFromAbove(raw, 'other-project')).toBeNull()
    expect(cleanFromAbove({ ...raw, story: '' }, SLUG)).toBeNull()
    expect(cleanFromAbove({ ...raw, frames: raw.frames.slice(0, 2) }, SLUG)).toBeNull()
  })

  it('shows nothing once the checked pin has moved away from where the pictures were taken', () => {
    const view = cleanFromAbove(raw, SLUG)
    expect(forPin(view, { lat: 18.5448, lon: 73.9686 })).not.toBeNull()   // a few metres
    expect(forPin(view, { lat: 18.5457, lon: 73.9685 })).toBeNull()       // about 100 m north
    expect(forPin(view, null)).toBeNull()
  })

  it('renders each year with its measured share, the code-written sentence and the credit', () => {
    const view = cleanFromAbove(raw, SLUG)!
    render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    expect(screen.getByRole('heading', { name: 'Kohinoor Riverdale from above, 2021 to 2026' })).toBeTruthy()
    expect(screen.getAllByRole('img')).toHaveLength(4)
    expect(screen.getByText('22% roofs, concrete')).toBeTruthy()
    expect(screen.getByText(raw.story)).toBeTruthy()
    const small = screen.getByText(/neighbouring plots/)
    expect(small.textContent).toContain('nothing is drawn in')
    expect(small.textContent).toContain('Copernicus Sentinel data')
  })

  it('reads the files the script wrote for the projects on the site', async () => {
    const dir = path.join(__dirname, '..', '..', 'public', 'from-above')
    const view = await readFromAbove(SLUG, dir)
    expect(view?.frames.length).toBeGreaterThanOrEqual(3)
    expect(view?.story).toMatch(/^Within 100 m of the map pin/)
    expect(await readFromAbove('../secrets', dir)).toBeNull()
  })

  it('plays the month-by-month loop only when its files are the project’s own, and names it for search', () => {
    const video = { src: `/from-above/${SLUG}.mp4`, poster: `/from-above/${SLUG}.webp`, width: 960, height: 540,
      from: '2021-01-20', to: '2026-11-11', months: 41 }
    expect(cleanFromAbove({ ...raw, video: { ...video, src: '/from-above/other.mp4' } }, SLUG)?.video).toBeNull()
    expect(cleanFromAbove({ ...raw, video: { ...video, months: 2 } }, SLUG)?.video).toBeNull()
    expect(cleanFromAbove(raw, SLUG)?.video).toBeNull()
    const view = cleanFromAbove({ ...raw, video }, SLUG)!
    const { container } = render(<ProjectFromAbove view={view} shown="Kohinoor Riverdale" siteUrl="https://avasetu.in" />)
    const el = screen.getByTestId('from-above-video') as HTMLVideoElement
    expect(el.getAttribute('poster')).toBe(video.poster)
    expect(el.muted).toBe(true)
    expect(el.getAttribute('src')).toBeNull()            // nothing downloads before it is near the screen
    expect(screen.getByText(/41 clear passes, October to May/)).toBeTruthy()
    expect(el.loop).toBe(false)                          // plays once and stops on the sentence
    expect(el.controls).toBe(true)
    const ld = JSON.parse(container.querySelector('script[type="application/ld+json"]')!.innerHTML)
    const vo = ld['@graph'].find((g: { '@type': string }) => g['@type'] === 'VideoObject')
    expect(vo.contentUrl).toBe('https://avasetu.in/from-above/kohinoor-riverdale-kharadi.mp4')
    expect(vo.name).toBe('Kohinoor Riverdale from above, Jan 2021 to Nov 2026')
  })

  it('shows what the daily pass stored under uploads, and nothing from anywhere else', () => {
    const dir = '/uploads/from_above/p52100056021'
    const rec = { ...raw, slug: undefined,
      frames: raw.frames.map((f) => ({ ...f, src: `${dir}/${f.year}.webp` })),
      video: { src: `${dir}/months.mp4`, poster: `${dir}/months.webp`, width: 960, height: 540, from: '2021-01-20', to: '2026-11-11', months: 41 } }
    const view = fromRecord(rec, SLUG)!
    expect(view.frames.map((f) => f.src)).toEqual([2021, 2022, 2023, 2026].map((y) => `${dir}/${y}.webp`))
    expect(view.video?.src).toBe(`${dir}/months.mp4`)
    const escaped = { ...rec, frames: rec.frames.map((f) => ({ ...f, src: `/uploads/from_above/x/../../${f.year}.webp` })) }
    expect(fromRecord(escaped, SLUG)).toBeNull()
    expect(fromRecord({ ...rec, video: { ...rec.video, poster: '/uploads/other.webp' } }, SLUG)?.video).toBeNull()
    expect(fromRecord(null, SLUG)).toBeNull()
  })
})

