import React from 'react'
import { render, screen, within } from '@testing-library/react'

// Area photos (docs/plan/area-pictures.md step 4): every photo shown says who took it and when, and a licensed one its licence
// and source; nothing is shown when there are none or the read fails.
const mockFetch = jest.fn()
jest.mock('@/lib/site/api', () => ({ fixturesForced: () => false, serverApiBase: () => 'http://api' }))

import AreaPhotos from '@/components/localities/AreaPhotos'
import { cleanAreaPhotos, getAreaPhotos, monthYear } from '@/components/localities/areaPhotoData'

const ID1 = 'a'.repeat(32)
const ID2 = 'b'.repeat(32)
const OWN = {
  id: ID1, url: `/uploads/area_photos/kharadi/${ID1}.webp`, small_url: `/uploads/area_photos/kharadi/${ID1}-small.webp`,
  width: 1600, height: 1067, caption: 'Kharadi bypass road at the EON IT Park signal', taken_on: '2026-11-10',
  credit: 'Rohan Kulkarni', kind: 'own', licence: null, licence_url: null, source_url: null,
}
const LICENSED = {
  ...OWN, id: ID2, url: `/uploads/area_photos/kharadi/${ID2}.webp`, small_url: `/uploads/area_photos/kharadi/${ID2}-small.webp`,
  caption: 'Ramwadi metro station, Aqua Line', taken_on: '2024-03-02', credit: 'Jane Doe', kind: 'licensed',
  licence: 'CC BY-SA 4.0', licence_url: 'https://creativecommons.org/licenses/by-sa/4.0/',
  source_url: 'https://commons.wikimedia.org/wiki/File:Ramwadi_metro.jpg',
}
const BODY = { area: { key: 'kharadi', name: 'Kharadi', slug: 'kharadi' }, photos: [OWN, LICENSED] }

function respond(status: number, body: unknown) {
  mockFetch.mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body })
}

beforeEach(() => {
  mockFetch.mockReset()
  global.fetch = mockFetch as unknown as typeof fetch
})

describe('reading the photos', () => {
  it('reads the area\'s live photos, revalidated, and keeps those with every credit field', async () => {
    respond(200, BODY)
    const photos = await getAreaPhotos('kharadi')
    expect(mockFetch.mock.calls[0][0]).toBe('http://api/api/v1/public/areas/kharadi/photos')
    expect(photos.map((p) => p.id)).toEqual([ID1, ID2])
  })

  it('gives no photo on a failure, a 404 or a body for another area', async () => {
    respond(500, {})
    expect(await getAreaPhotos('kharadi')).toEqual([])
    respond(404, {})
    expect(await getAreaPhotos('kharadi')).toEqual([])
    mockFetch.mockRejectedValue(new Error('down'))
    expect(await getAreaPhotos('kharadi')).toEqual([])
    expect(cleanAreaPhotos(BODY, 'wagholi')).toEqual([])
    expect(cleanAreaPhotos('nope', 'kharadi')).toEqual([])
  })

  it('drops a photo without its credit, a licensed one without licence or source, and one that is not our copy', () => {
    const bad = [
      { ...OWN, credit: '' },
      { ...LICENSED, licence_url: 'https://example.com/licence' },
      { ...LICENSED, source_url: 'http://commons.wikimedia.org/x' },
      { ...OWN, url: 'https://portal.example.com/photo.jpg' },
      { ...OWN, taken_on: 'recently' },
    ]
    expect(cleanAreaPhotos({ ...BODY, photos: bad }, 'kharadi')).toEqual([])
  })

  it('says the month a photo was taken', () => {
    expect(monthYear('2026-11-10')).toBe('November 2026')
    expect(monthYear('bad')).toBe('')
  })
})

describe('the photos on the area guide', () => {
  it('shows each photo as a figure with its caption, who took it and when, and a licensed one\'s licence and source linked', () => {
    const { container } = render(<AreaPhotos name="Kharadi" photos={cleanAreaPhotos(BODY, 'kharadi')} />)
    const s = screen.getByRole('region', { name: 'Kharadi in photos' })
    const figures = s.querySelectorAll('figure')
    expect(figures).toHaveLength(2)
    const [own, lic] = Array.from(figures)
    expect(within(own as HTMLElement).getByRole('img', { name: OWN.caption })).toHaveAttribute('loading', 'eager')
    expect(own.querySelector('figcaption')).toHaveTextContent('Kharadi bypass road at the EON IT Park signal · Photo: Rohan Kulkarni, November 2026')
    expect(own.querySelector('figcaption')).not.toHaveTextContent(/CC|via/)
    const img = within(lic as HTMLElement).getByRole('img', { name: LICENSED.caption })
    expect(img).toHaveAttribute('loading', 'lazy')
    expect(img).toHaveAttribute('width', '1600')
    expect(lic.querySelector('figcaption')).toHaveTextContent('Photo: Jane Doe, March 2024 · CC BY-SA 4.0, via Wikimedia Commons')
    expect(within(lic as HTMLElement).getByRole('link', { name: 'CC BY-SA 4.0' })).toHaveAttribute('href', LICENSED.licence_url)
    expect(within(lic as HTMLElement).getByRole('link', { name: 'Wikimedia Commons' })).toHaveAttribute('href', LICENSED.source_url)

    const ld = JSON.parse(container.querySelector('script[type="application/ld+json"]')!.innerHTML)
    const [ownLd, licLd] = ld['@graph']
    expect(licLd).toMatchObject({
      '@type': 'ImageObject', creditText: 'Jane Doe', creator: { '@type': 'Person', name: 'Jane Doe' }, dateCreated: '2024-03-02',
      license: LICENSED.licence_url, acquireLicensePage: LICENSED.source_url, caption: LICENSED.caption,
    })
    expect(licLd.contentUrl).toMatch(new RegExp(`^https?://[^/]+/uploads/area_photos/kharadi/${ID2}\\.webp$`))
    expect(ownLd).toMatchObject({ creditText: 'Rohan Kulkarni', dateCreated: '2026-11-10' })
    expect(ownLd.license).toBeUndefined()
  })

  it('renders nothing when there are no photos', () => {
    const { container } = render(<AreaPhotos name="Kharadi" photos={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})
