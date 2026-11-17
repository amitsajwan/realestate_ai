/** Typed client, rules and fixtures for Studio > Area photos (backend /area-photos, app/modules/areaphotos). */
import { API_BASE_URL } from '@shared/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export type PhotoKind = 'own' | 'licensed'
export type PhotoStatus = 'pending' | 'live' | 'hidden'

/** The free licences a photo may carry (backend areaphotos/service.py LICENCES); anything else is refused there too. */
export const LICENCES = ['CC BY 4.0', 'CC BY-SA 4.0', 'CC0', 'CC BY 3.0', 'CC BY-SA 3.0', 'CC BY 2.0', 'CC BY-SA 2.0'] as const
export const CAPTION_MIN = 8
export const CAPTION_MAX = 160
export const CREDIT_MAX = 80

export interface AreaPhotoItem {
  id: string
  area: string
  url: string
  small_url: string
  width: number
  height: number
  caption: string
  taken_on: string
  credit: string
  kind: PhotoKind
  licence: string | null
  licence_url: string | null
  source_url: string | null
  status: PhotoStatus
  order: number
  created_by: string | null
  created_at: string | null
  mine: boolean
  can_edit: boolean
}
export interface AreaPhotoList {
  area: { key: string; name: string; slug: string }
  items: AreaPhotoItem[]
  can_publish: boolean
}
/** What is written about a photo: the same for every photo of one upload, except the caption. */
export interface PhotoFacts {
  caption: string
  taken_on: string
  credit: string
  kind: PhotoKind
  licence: string
  source_url: string
}

/** What is missing before a photo can be sent, in plain words; null when it may go (the server checks again). */
export function factsProblem(f: PhotoFacts, today: string): string | null {
  const caption = f.caption.trim()
  if (caption.length < CAPTION_MIN || caption.length > CAPTION_MAX) return `Write a caption of ${CAPTION_MIN} to ${CAPTION_MAX} letters: what the photo shows and where.`
  if (!f.credit.trim()) return 'Say who took the photo.'
  if (!/^\d{4}-\d{2}-\d{2}$/.test(f.taken_on)) return 'Give the date the photo was taken.'
  if (f.taken_on > today) return 'The date taken cannot be in the future.'
  if (f.kind === 'licensed') {
    if (!(LICENCES as readonly string[]).includes(f.licence)) return 'Choose the photo\'s licence.'
    if (!/^https:\/\/[^\s/]+\.[^\s/]+\/\S*$/.test(f.source_url.trim())) return 'Paste the https link to the page the photo came from.'
  }
  return null
}

export interface AreaPhotosApi {
  list(area: string): Promise<AreaPhotoList>
  upload(area: string, file: File, facts: PhotoFacts): Promise<AreaPhotoItem>
  edit(id: string, changes: Partial<PhotoFacts>): Promise<AreaPhotoItem>
  publish(id: string): Promise<AreaPhotoItem>
  hide(id: string): Promise<AreaPhotoItem>
  reorder(area: string, ids: string[]): Promise<AreaPhotoItem[]>
}

export function createAreaPhotosApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): AreaPhotosApi {
  const base = opts.baseUrl ?? API_BASE_URL
  async function request<T>(path: string, init: { method?: string; json?: unknown; form?: FormData } = {}): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    const token = opts.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
    let body: string | FormData | undefined = init.form
    if (init.json !== undefined) {
      headers['Content-Type'] = 'application/json'
      body = JSON.stringify(init.json)
    }
    let res: Response
    try {
      res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1/area-photos${path}`, { method: init.method ?? 'GET', headers, body })
    } catch {
      throw new ApiError(0, 'Cannot reach the server. Check your internet.')
    }
    const text = await res.text()
    let data: unknown = null
    if (text) {
      try {
        data = JSON.parse(text)
      } catch {
        data = { detail: text.slice(0, 200) }
      }
    }
    if (!res.ok) throw parseErrorBody(data, res.status)
    return data as T
  }
  const one = (id: string) => `/${encodeURIComponent(id)}`
  return {
    list: (area) => request<AreaPhotoList>(`?area=${encodeURIComponent(area)}`),
    upload: (area, file, facts) => {
      const form = new FormData()
      form.append('file', file)
      form.append('area', area)
      for (const [k, v] of Object.entries(facts)) form.append(k, facts.kind === 'own' && (k === 'licence' || k === 'source_url') ? '' : v.trim())
      return request<AreaPhotoItem>('', { method: 'POST', form })
    },
    edit: (id, changes) => request<AreaPhotoItem>(one(id), { method: 'PATCH', json: changes }),
    publish: (id) => request<AreaPhotoItem>(`${one(id)}/publish`, { method: 'POST' }),
    hide: (id) => request<AreaPhotoItem>(`${one(id)}/hide`, { method: 'POST' }),
    reorder: async (area, ids) => (await request<{ items: AreaPhotoItem[] }>('/order', { method: 'PUT', json: { area, ids } })).items ?? [],
  }
}

// ---- fixtures (local/dev mode) ----
const FX_PICTURE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect width='400' height='300' fill='%23cbd5e1'/%3E%3C/svg%3E"

export function createFixtureAreaPhotosApi(): AreaPhotosApi {
  let items: AreaPhotoItem[] = [{
    id: 'fx-p1', area: 'kharadi', url: FX_PICTURE, small_url: FX_PICTURE, width: 400, height: 300,
    caption: 'Kharadi bypass road at the EON IT Park signal', taken_on: '2026-11-10', credit: 'Avasetu team', kind: 'own',
    licence: null, licence_url: null, source_url: null, status: 'live', order: 0, created_by: 'owner', created_at: '2026-11-10T06:00:00Z',
    mine: true, can_edit: true,
  }]
  const find = (id: string) => {
    const p = items.find((x) => x.id === id)
    if (!p) throw new ApiError(404, 'Photo not found.')
    return p
  }
  const sorted = (area: string) => items.filter((p) => p.area === area).sort((a, b) => a.order - b.order)
  return {
    list: async (area) => ({ area: { key: area, name: area, slug: area.replace(/_/g, '-') }, items: sorted(area), can_publish: true }),
    upload: async (area, file, facts) => {
      const p: AreaPhotoItem = {
        id: `fx-${Date.now()}-${items.length}`, area, url: URL.createObjectURL(file), small_url: URL.createObjectURL(file), width: 1600, height: 1200,
        ...facts, licence: facts.kind === 'licensed' ? facts.licence : null, licence_url: null,
        source_url: facts.kind === 'licensed' ? facts.source_url : null, status: 'pending',
        order: Math.min(0, ...sorted(area).map((x) => x.order)) - 1, created_by: 'owner', created_at: new Date().toISOString(), mine: true, can_edit: true,
      }
      items = [...items, p]
      return p
    },
    edit: async (id, changes) => Object.assign(find(id), changes),
    publish: async (id) => Object.assign(find(id), { status: 'live' as const }),
    hide: async (id) => Object.assign(find(id), { status: 'hidden' as const }),
    reorder: async (area, ids) => {
      ids.forEach((id, i) => (find(id).order = i))
      return sorted(area)
    },
  }
}

const real = createAreaPhotosApi({ getToken })
let fake: AreaPhotosApi | null = null
const impl = (): AreaPhotosApi => (isFixtureMode() ? (fake ??= createFixtureAreaPhotosApi()) : real)

/** What the screen imports: the fixture API in fixture mode, else the real one. */
export const areaPhotosApi: AreaPhotosApi = {
  list: (a) => impl().list(a),
  upload: (a, f, facts) => impl().upload(a, f, facts),
  edit: (id, c) => impl().edit(id, c),
  publish: (id) => impl().publish(id),
  hide: (id) => impl().hide(id),
  reorder: (a, ids) => impl().reorder(a, ids),
}
