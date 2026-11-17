/**
 * areaPictures.ts reading GET /api/v1/public/areas/{slug}/pictures (backend areastats.pictures, docs/plan/area-pictures.md
 * step 3), with the by-hand script's public/areas/<slug>.json kept as a fallback.
 */
import os from 'os'
import path from 'path'
import { promises as fs } from 'fs'
import { cleanApiPictures, readAreaPictures } from '@/components/localities/areaPictures'

jest.mock('@/lib/site/api', () => ({ fixturesForced: jest.fn(() => false), serverApiBase: () => 'http://api' }))
const { fixturesForced } = jest.requireMock('@/lib/site/api') as { fixturesForced: jest.Mock }

const API_BODY = {
  area: { key: 'kharadi', name: 'Kharadi', slug: 'kharadi' },
  pictures: [
    { year: 2017, captured_on: '2017-03-12', src: '/uploads/area_pictures/kharadi-2017.webp', width: 1000, height: 994 },
    { year: 2026, captured_on: '2026-02-18', src: '/uploads/area_pictures/kharadi-2026.webp', width: 1000, height: 994 },
  ],
}

beforeEach(() => {
  fixturesForced.mockReturnValue(false)
  global.fetch = jest.fn() as unknown as typeof fetch
})

describe('cleanApiPictures', () => {
  it('keeps only entries whose year, day and file name agree, with the right credit', () => {
    const got = cleanApiPictures(API_BODY, 'kharadi')
    expect(got).toEqual([
      { year: 2017, src: '/uploads/area_pictures/kharadi-2017.webp', width: 1000, height: 994, day: '2017-03-12',
        credit: 'Contains modified Copernicus Sentinel data 2017' },
      { year: 2026, src: '/uploads/area_pictures/kharadi-2026.webp', width: 1000, height: 994, day: '2026-02-18',
        credit: 'Contains modified Copernicus Sentinel data 2026' },
    ])
  })

  it('drops a list for another area, a bad file name, or a day that disagrees with its year', () => {
    expect(cleanApiPictures(API_BODY, 'wagholi')).toEqual([])
    const badSrc = { ...API_BODY, pictures: [{ ...API_BODY.pictures[0], src: '/areas/kharadi-2017.webp' }] }
    expect(cleanApiPictures(badSrc, 'kharadi')).toEqual([])
    const badYear = { ...API_BODY, pictures: [{ ...API_BODY.pictures[0], captured_on: '2018-03-12' }] }
    expect(cleanApiPictures(badYear, 'kharadi')).toEqual([])
    expect(cleanApiPictures(null, 'kharadi')).toEqual([])
    expect(cleanApiPictures({ area: { slug: 'kharadi' } }, 'kharadi')).toEqual([])
  })
})

describe('readAreaPictures', () => {
  it('reads the live pictures from the API when it answers', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({ ok: true, status: 200, json: async () => API_BODY })
    const got = await readAreaPictures('kharadi')
    expect(got.map((p) => p.year)).toEqual([2017, 2026])
    expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe('http://api/api/v1/public/areas/kharadi/pictures')
  })

  it('falls back to the public/areas/<slug>.json file when the API answers nothing usable', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({ ok: true, status: 200, json: async () => ({ area: { slug: 'kharadi' } }) })
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'areas-'))
    const sidecar = {
      area: 'kharadi', pictures: [{ year: 2017, src: '/areas/kharadi-2017.webp', width: 1000, height: 994,
        captured: { from: '2017-03-12' } }],
    }
    await fs.writeFile(path.join(dir, 'kharadi.json'), JSON.stringify(sidecar))
    const got = await readAreaPictures('kharadi', dir)
    expect(got.map((p) => p.year)).toEqual([2017])
  })

  it('falls back to the file when the API call fails outright, and gives [] when neither has anything', async () => {
    ;(global.fetch as jest.Mock).mockRejectedValue(new Error('network down'))
    const emptyDir = await fs.mkdtemp(path.join(os.tmpdir(), 'areas-'))
    expect(await readAreaPictures('kharadi', emptyDir)).toEqual([])
  })

  it('never calls the API in fixture mode, going straight to the file', async () => {
    fixturesForced.mockReturnValue(true)
    const emptyDir = await fs.mkdtemp(path.join(os.tmpdir(), 'areas-'))
    expect(await readAreaPictures('kharadi', emptyDir)).toEqual([])
    expect(global.fetch).not.toHaveBeenCalled()
  })
})
