import React from 'react'
import path from 'path'
import { render, screen } from '@testing-library/react'
import ProjectFromAbove from '@/components/site/ProjectFromAbove'
import { cleanFromAbove, forPin, readFromAbove } from '@/lib/site/fromAbove'

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
})
