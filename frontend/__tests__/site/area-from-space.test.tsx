import React from 'react'
import { render, screen } from '@testing-library/react'
import AreaFromSpace from '@/components/localities/AreaFromSpace'
import { areaFromRecord, cleanAreaItems } from '@/lib/site/areaFromSpace'
import { videoSitemapXml } from '@/lib/site/videoSitemap'

const DIR = '/uploads/area_space/kharadi'
const frame = (year: number) => ({ year, day: `${year}-02-15`, src: `${DIR}/${year}.webp`, width: 960, height: 960 })
const video = { src: `${DIR}/months.mp4`, poster: `${DIR}/months.webp`, width: 720, height: 720, from: '2019-01-01', to: '2026-11-01', months: 60 }
const raw = {
  area: { key: 'kharadi', name: 'Kharadi', slug: 'kharadi' }, middle: { lat: 18.551, lon: 73.948 }, side_km: 5.5,
  story: 'Fields in the east gave way to blocks of buildings after 2022.',
  where: 'Each picture is 5.5 km across, north up, centred on the middle of Kharadi, at 10 m a pixel.',
  credit: 'Contains modified Copernicus Sentinel data 2019-2026',
  frames: [frame(2019), frame(2022), frame(2024), frame(2026)], video, updated: '2026-11-21',
  seasons: [{ label: 'Jan-Mar 2019', day: '2019-01-01', line: 'Open fields across the east.' },
    { label: 'Oct-Dec 2026', day: '2026-10-01', line: 'New blocks of buildings in the north-east.' }],
}

describe('an area from space', () => {
  it('keeps only the pictures and video stored for this area', () => {
    const bad = { ...raw, frames: [...raw.frames, { ...frame(2025), src: '/uploads/area_space/wagholi/2025.webp' },
      { ...frame(2023), src: '/uploads/from_above/p1/2023.webp' }] }
    expect(areaFromRecord(bad, 'kharadi')?.frames.map((f) => f.year)).toEqual([2019, 2022, 2024, 2026])
    expect(areaFromRecord({ ...raw, video: { ...video, src: '/uploads/area_space/wagholi/months.mp4' } }, 'kharadi')?.video).toBeNull()
    expect(areaFromRecord(raw, 'wagholi')).toBeNull()      // another area's answer
  })

  it('shows nothing without a sentence, with fewer than three years, or for nothing at all', () => {
    expect(areaFromRecord({ ...raw, story: '' }, 'kharadi')).toBeNull()
    expect(areaFromRecord({ ...raw, frames: raw.frames.slice(0, 2) }, 'kharadi')).toBeNull()
    expect(areaFromRecord(null, 'kharadi')).toBeNull()
  })

  it('puts the video, the summary and the newest season on the area guide, linking to its watch page', () => {
    render(<AreaFromSpace view={areaFromRecord(raw, 'kharadi')} />)
    expect(screen.getByRole('heading', { name: 'Kharadi from space' })).toBeTruthy()
    expect(screen.getByTestId('from-above-video').getAttribute('poster')).toBe(`${DIR}/months.webp`)
    expect(screen.getByText(/60 clear months of the Sentinel-2 satellite, Jan 2019 to Nov 2026, 5.5 km across/)).toBeTruthy()
    expect(screen.getByText('New blocks of buildings in the north-east.')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Every season of Kharadi from space' }).getAttribute('href')).toBe('/localities/kharadi/from-space')
  })

  it('shows no section without a video', () => {
    const { container } = render(<AreaFromSpace view={areaFromRecord({ ...raw, video: null }, 'kharadi')} />)
    expect(container.innerHTML).toBe('')
  })

  it('lists areas only with their own files, and puts their watch pages in the video sitemap first', () => {
    const item = { slug: 'kharadi', name: 'Kharadi', story: 'Fields gave way to buildings.', picture: `${DIR}/2026.webp`,
      video: { src: video.src, poster: video.poster, from: video.from, to: video.to, months: 60 }, years: [2019, 2026], updated: '2026-11-21', seasons: 23 }
    const items = cleanAreaItems([item, { ...item, slug: 'wagholi' }, { ...item, slug: '../x' }, null])
    expect(items.map((x) => x.slug)).toEqual(['kharadi'])
    const xml = videoSitemapXml('https://avasetu.in', [], items)
    expect(xml).toContain('<loc>https://avasetu.in/localities/kharadi/from-space</loc>')
    expect(xml).toContain('<video:title>Kharadi, Pune from space, 2019 to 2026</video:title>')
    expect(xml).toContain(`<video:content_loc>https://avasetu.in${DIR}/months.mp4</video:content_loc>`)
  })
})
