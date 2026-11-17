import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import AreaPhotosPage from '@/app/studio/area-photos/page'
import { createAreaPhotosApi, factsProblem } from '@/lib/app/areaPhotos'
import type { AreaPhotoItem, AreaPhotoList } from '@/lib/app/areaPhotos'

const mockApi: Record<string, jest.Mock> = {}
;['list', 'upload', 'edit', 'publish', 'hide', 'refuse', 'publishAll', 'reorder'].forEach((n) => (mockApi[n] = jest.fn()))

jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok' }))
jest.mock('@/lib/app/client', () => ({ errorMessage: (e: Error) => e.message, isFixtureMode: () => false }))
jest.mock('@/lib/app/imageCompress', () => ({ compressImage: async (f: File) => f }))
jest.mock('@/lib/app/areaPhotos', () => ({
  ...jest.requireActual('@/lib/app/areaPhotos'),
  areaPhotosApi: new Proxy({}, { get: (_t, k: string) => (...a: unknown[]) => mockApi[k](...a) }),
}))

const photo = (id: string, status: AreaPhotoItem['status'], over: Partial<AreaPhotoItem> = {}): AreaPhotoItem => ({
  id, area: 'kharadi', url: `/uploads/area_photos/kharadi/${id}.webp`, small_url: `/uploads/area_photos/kharadi/${id}-small.webp`,
  width: 1600, height: 1067, caption: `Kharadi photo ${id}`, taken_on: '2026-11-10', credit: 'Rohan', kind: 'own', licence: null,
  licence_url: null, source_url: null, status, order: 0, created_by: 'a1', created_at: null, mine: true, can_edit: true,
  origin: 'upload', ai: null, ...over,
})
const list = (items: AreaPhotoItem[], can_publish = true): AreaPhotoList => ({ area: { key: 'kharadi', name: 'Kharadi', slug: 'kharadi' }, items, can_publish })

beforeEach(() => Object.values(mockApi).forEach((m) => m.mockReset()))

describe('Studio > Area photos', () => {
  it('the owner publishes a waiting photo, hides a live one and moves one up', async () => {
    mockApi.list.mockResolvedValue(list([photo('p1', 'live'), photo('p2', 'pending')]))
    mockApi.publish.mockResolvedValue(photo('p2', 'live'))
    mockApi.hide.mockResolvedValue(photo('p1', 'hidden'))
    mockApi.reorder.mockResolvedValue([])
    render(<AreaPhotosPage />)
    const rows = await screen.findAllByTestId('area-photo-row')
    expect(mockApi.list).toHaveBeenCalledWith('kharadi')
    expect(rows[1]).toHaveTextContent('Waiting for the owner')
    fireEvent.click(within(rows[1]).getByTestId('area-photo-publish'))
    await waitFor(() => expect(mockApi.publish).toHaveBeenCalledWith('p2'))
    fireEvent.click(within((await screen.findAllByTestId('area-photo-row'))[0]).getByTestId('area-photo-hide'))
    await waitFor(() => expect(mockApi.hide).toHaveBeenCalledWith('p1'))
    fireEvent.click(within((await screen.findAllByTestId('area-photo-row'))[1]).getByRole('button', { name: 'Move up' }))
    await waitFor(() => expect(mockApi.reorder).toHaveBeenCalledWith('kharadi', ['p2', 'p1']))
  })

  it('an agent sees no publish, hide or order buttons', async () => {
    mockApi.list.mockResolvedValue(list([photo('p2', 'pending')], false))
    render(<AreaPhotosPage />)
    const [row] = await screen.findAllByTestId('area-photo-row')
    expect(within(row).queryByTestId('area-photo-publish')).toBeNull()
    expect(within(row).queryByRole('button', { name: 'Move up' })).toBeNull()
  })

  it('shows the photo scout\'s suggestions with their reason, and the owner publishes or refuses one', async () => {
    const suggested = photo('s1', 'suggested', {
      origin: 'scout', kind: 'licensed', licence: 'CC BY-SA 4.0', source_url: 'https://commons.wikimedia.org/wiki/File:x.jpg',
      ai: { score: 4, shows: ['metro'], reason: "Shows Kharadi's metro; taken March 2024; CC BY-SA 4.0." },
    })
    mockApi.list.mockResolvedValue(list([photo('p1', 'live'), suggested]))
    mockApi.refuse.mockResolvedValue({ ...suggested, status: 'refused' })
    render(<AreaPhotosPage />)
    const section = await screen.findByTestId('area-photos-suggested')
    expect(section).toHaveTextContent("Shows Kharadi's metro; taken March 2024; CC BY-SA 4.0.")
    const [row] = within(section).getAllByTestId('area-photo-row')
    expect(within(row).getByTestId('area-photo-publish')).toBeInTheDocument()
    fireEvent.click(within(row).getByTestId('area-photo-refuse'))
    await waitFor(() => expect(mockApi.refuse).toHaveBeenCalledWith('s1'))
  })

  it('the owner publishes every suggested photo at once', async () => {
    mockApi.list.mockResolvedValue(list([photo('s1', 'suggested', { origin: 'scout' }), photo('s2', 'suggested', { origin: 'scout' })]))
    mockApi.publishAll.mockResolvedValue([])
    render(<AreaPhotosPage />)
    await screen.findByTestId('area-photos-suggested')
    fireEvent.click(screen.getByTestId('area-photo-publish-all'))
    await waitFor(() => expect(mockApi.publishAll).toHaveBeenCalledWith('kharadi'))
  })

  it('an agent sees suggestions read-only, with no publish-all button', async () => {
    mockApi.list.mockResolvedValue(list([photo('s1', 'suggested', { origin: 'scout' })], false))
    render(<AreaPhotosPage />)
    const section = await screen.findByTestId('area-photos-suggested')
    expect(within(section).queryByTestId('area-photo-publish')).toBeNull()
    expect(within(section).queryByTestId('area-photo-refuse')).toBeNull()
    expect(screen.queryByTestId('area-photo-publish-all')).toBeNull()
  })

  it('sends a licensed photo only with its licence and link', async () => {
    mockApi.list.mockResolvedValue(list([]))
    mockApi.upload.mockResolvedValue(photo('p3', 'pending'))
    render(<AreaPhotosPage />)
    await screen.findByText(/No photos of Kharadi yet/)
    const file = new File(['x'], 'metro.jpg', { type: 'image/jpeg' })
    fireEvent.change(screen.getByTestId('area-photo-files'), { target: { files: [file] } })
    fireEvent.change(screen.getByTestId('area-photo-caption'), { target: { value: 'Ramwadi metro station, Aqua Line' } })
    fireEvent.change(screen.getByTestId('area-photo-date'), { target: { value: '2024-03-02' } })
    fireEvent.change(screen.getByTestId('area-photo-credit'), { target: { value: 'Jane Doe' } })
    fireEvent.click(screen.getByLabelText(/Free-licensed/))
    fireEvent.click(screen.getByTestId('area-photo-send'))
    expect(await screen.findByText("Choose the photo's licence.")).toBeInTheDocument()
    expect(mockApi.upload).not.toHaveBeenCalled()
    fireEvent.change(screen.getByTestId('area-photo-licence'), { target: { value: 'CC BY-SA 4.0' } })
    fireEvent.change(screen.getByTestId('area-photo-source'), { target: { value: 'https://commons.wikimedia.org/wiki/File:Ramwadi.jpg' } })
    fireEvent.click(screen.getByTestId('area-photo-send'))
    await waitFor(() => expect(mockApi.upload).toHaveBeenCalledWith('kharadi', file, {
      caption: 'Ramwadi metro station, Aqua Line', taken_on: '2024-03-02', credit: 'Jane Doe', kind: 'licensed',
      licence: 'CC BY-SA 4.0', source_url: 'https://commons.wikimedia.org/wiki/File:Ramwadi.jpg',
    }))
  })
})

describe('the area photos client', () => {
  it('uploads as multipart to /area-photos and leaves an own photo without licence or link', async () => {
    const fetchImpl = jest.fn(async () => ({ ok: true, status: 201, text: async () => JSON.stringify(photo('p1', 'pending')) })) as unknown as typeof fetch
    const api = createAreaPhotosApi({ getToken: () => 'tok', baseUrl: 'http://api', fetchImpl })
    await api.upload('kharadi', new File(['x'], 'a.jpg', { type: 'image/jpeg' }),
      { caption: 'Kharadi road', taken_on: '2026-11-10', credit: 'Me', kind: 'own', licence: 'CC0', source_url: 'https://x.in/a' })
    const [url, init] = (fetchImpl as jest.Mock).mock.calls[0]
    expect(url).toBe('http://api/api/v1/area-photos')
    expect(init.method).toBe('POST')
    expect(init.headers.Authorization).toBe('Bearer tok')
    const form = init.body as FormData
    expect(form.get('area')).toBe('kharadi')
    expect(form.get('licence')).toBe('')
    expect(form.get('source_url')).toBe('')
  })

  it('says what is missing before sending', () => {
    const ok = { caption: 'Kharadi bypass road', taken_on: '2026-11-10', credit: 'Me', kind: 'own' as const, licence: '', source_url: '' }
    expect(factsProblem(ok, '2026-11-17')).toBeNull()
    expect(factsProblem({ ...ok, taken_on: '2026-11-18' }, '2026-11-17')).toMatch(/future/)
    expect(factsProblem({ ...ok, kind: 'licensed', licence: 'CC BY 4.0', source_url: 'http://x.in/a' }, '2026-11-17')).toMatch(/https/)
  })
})
