/** Typed client, types and fixtures for Studio > Admin > Pictures from above (backend /area-pictures, app/modules/areastats/
 *  pictures.py, docs/plan/area-pictures.md step 3). The owner approves or refuses what the AI judge and the code checks
 *  picked; approving an area's first picture lets later ones, once both pass, go live by themselves. */
import { API_BASE_URL } from '@shared/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export type PictureStatus = 'pending' | 'live' | 'refused' | 'superseded'

export interface Judged {
  ok: boolean
  reason: string
  model: string
}

export interface AreaPictureItem {
  id: string
  area: string
  year: number
  captured_on: string
  url: string
  width: number
  height: number
  cloud_pct: number | null
  judged: Judged | null
  status: PictureStatus
  created_at: string | null
}

export interface AreaPictureList {
  area: { key: string; name: string; slug: string }
  trusted: boolean
  items: AreaPictureItem[]
}

export interface AreaPicturesApi {
  list(area: string): Promise<AreaPictureList>
  decide(id: string, live: boolean): Promise<AreaPictureItem>
}

export function createAreaPicturesApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): AreaPicturesApi {
  const base = opts.baseUrl ?? API_BASE_URL
  async function request<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    const token = opts.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
    let body: string | undefined
    if (init.json !== undefined) {
      headers['Content-Type'] = 'application/json'
      body = JSON.stringify(init.json)
    }
    let res: Response
    try {
      res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1/area-pictures${path}`, { method: init.method ?? 'GET', headers, body })
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
  return {
    list: (area) => request<AreaPictureList>(`?area=${encodeURIComponent(area)}`),
    decide: (id, live) => request<AreaPictureItem>(`/${encodeURIComponent(id)}/decide`, { method: 'POST', json: { live } }),
  }
}

// ---- fixtures (local/dev mode) ----
const FX_PICTURE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect width='400' height='300' fill='%236b7f5e'/%3E%3C/svg%3E"

export function createFixtureAreaPicturesApi(): AreaPicturesApi {
  let items: AreaPictureItem[] = [
    { id: 'fx-1', area: 'kharadi', year: 2017, captured_on: '2017-03-12', url: FX_PICTURE, width: 1000, height: 994,
      cloud_pct: 2.1, judged: { ok: true, reason: 'Clear, ground plainly visible', model: 'gemini' }, status: 'pending',
      created_at: '2026-11-10T06:00:00Z' },
    { id: 'fx-2', area: 'kharadi', year: 2026, captured_on: '2026-02-18', url: FX_PICTURE, width: 1000, height: 994,
      cloud_pct: 0.5, judged: { ok: true, reason: 'Clear', model: 'gemini' }, status: 'pending', created_at: '2026-11-15T06:00:00Z' },
  ]
  let trusted = false
  return {
    list: async (area) => ({ area: { key: area, name: area, slug: area.replace(/_/g, '-') },
      trusted, items: items.filter((p) => p.area === area) }),
    decide: async (id, live) => {
      const p = items.find((x) => x.id === id)
      if (!p) throw new ApiError(404, 'Picture not found.')
      p.status = live ? 'live' : 'refused'
      if (live) trusted = true
      return p
    },
  }
}

const real = createAreaPicturesApi({ getToken })
let fake: AreaPicturesApi | null = null
const impl = (): AreaPicturesApi => (isFixtureMode() ? (fake ??= createFixtureAreaPicturesApi()) : real)

/** What the screen imports: the fixture API in fixture mode, else the real one. */
export const areaPicturesApi: AreaPicturesApi = {
  list: (area) => impl().list(area),
  decide: (id, live) => impl().decide(id, live),
}
