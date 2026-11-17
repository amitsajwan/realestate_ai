import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { AreaPicturesReview } from '@/components/app/admin/AreaPicturesReview'
import { createAreaPicturesApi } from '@/lib/app/areaPictures'
import type { AreaPictureItem, AreaPictureList } from '@/lib/app/areaPictures'

const mockApi: Record<string, jest.Mock> = {}
;['list', 'decide'].forEach((n) => (mockApi[n] = jest.fn()))

jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok' }))
jest.mock('@/lib/app/client', () => ({ errorMessage: (e: Error) => e.message, isFixtureMode: () => false }))
jest.mock('@/lib/app/areaPictures', () => ({
  ...jest.requireActual('@/lib/app/areaPictures'),
  areaPicturesApi: new Proxy({}, { get: (_t, k: string) => (...a: unknown[]) => mockApi[k](...a) }),
}))

const picture = (id: string, year: number, status: AreaPictureItem['status'], over: Partial<AreaPictureItem> = {}): AreaPictureItem => ({
  id, area: 'kharadi', year, captured_on: `${year}-03-12`, url: `/uploads/area_pictures/kharadi-${year}.webp`,
  width: 1000, height: 994, cloud_pct: 1.2, judged: { ok: true, reason: 'Clear', model: 'gemini' }, status,
  created_at: null, ...over,
})
const list = (items: AreaPictureItem[], trusted = false): AreaPictureList => ({
  area: { key: 'kharadi', name: 'Kharadi', slug: 'kharadi' }, trusted, items,
})

beforeEach(() => Object.values(mockApi).forEach((m) => m.mockReset()))

describe('Studio > Admin > Pictures from above', () => {
  it('the owner approves a waiting picture, which sets trust, and refuses another', async () => {
    mockApi.list.mockResolvedValue(list([picture('p1', 2017, 'pending'), picture('p2', 2026, 'pending')]))
    mockApi.decide.mockResolvedValue(picture('p1', 2017, 'live'))
    render(<AreaPicturesReview />)
    const cards = await screen.findAllByTestId('area-picture')
    expect(mockApi.list).toHaveBeenCalledWith('kharadi')
    expect(cards[0]).toHaveTextContent('Waiting for you')
    fireEvent.click(within(cards[0]).getByTestId('area-picture-approve'))
    await waitFor(() => expect(mockApi.decide).toHaveBeenCalledWith('p1', true))

    mockApi.decide.mockResolvedValue(picture('p2', 2026, 'refused'))
    fireEvent.click(within((await screen.findAllByTestId('area-picture'))[1]).getByTestId('area-picture-refuse'))
    await waitFor(() => expect(mockApi.decide).toHaveBeenCalledWith('p2', false))
  })

  it('shows the judge\'s doubt, and offers no buttons for a picture that is already live or refused', async () => {
    mockApi.list.mockResolvedValue(list([
      picture('p1', 2017, 'live'),
      picture('p2', 2026, 'pending', { judged: { ok: false, reason: 'haze over the box', model: 'gemini' } }),
    ], true))
    render(<AreaPicturesReview />)
    const cards = await screen.findAllByTestId('area-picture')
    expect(within(cards[0]).queryByTestId('area-picture-approve')).toBeNull()
    expect(cards[1]).toHaveTextContent('haze over the box')
    expect(within(cards[1]).getByTestId('area-picture-approve')).toBeInTheDocument()
  })

  it('says when a picture had no model judgement at all', async () => {
    mockApi.list.mockResolvedValue(list([picture('p1', 2017, 'pending', { judged: null })]))
    render(<AreaPicturesReview />)
    expect(await screen.findByText(/code checks alone kept it/)).toBeInTheDocument()
  })

  it('shows nothing-to-review when the area has no pictures', async () => {
    mockApi.list.mockResolvedValue(list([]))
    render(<AreaPicturesReview />)
    expect(await screen.findByTestId('area-pictures-empty')).toHaveTextContent('No pictures')
  })
})

describe('the area pictures client', () => {
  it('lists with the area query and posts the decide action', async () => {
    const fetchImpl = jest.fn(async () => ({ ok: true, status: 200, text: async () => JSON.stringify(picture('p1', 2017, 'live')) })) as unknown as typeof fetch
    const api = createAreaPicturesApi({ getToken: () => 'tok', baseUrl: 'http://api', fetchImpl })
    await api.list('kharadi')
    expect((fetchImpl as jest.Mock).mock.calls[0][0]).toBe('http://api/api/v1/area-pictures?area=kharadi')
    await api.decide('p1', true)
    const [url, init] = (fetchImpl as jest.Mock).mock.calls[1]
    expect(url).toBe('http://api/api/v1/area-pictures/p1/decide')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({ live: true })
    expect(init.headers.Authorization).toBe('Bearer tok')
  })
})
