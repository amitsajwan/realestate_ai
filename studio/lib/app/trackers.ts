import { API_BASE_URL } from '@shared/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

/** One report attached to a tracker, as the owner sees it (hidden ones too, so a hide can be undone). */
export interface DeskReport { id: string; date: string; title: string; source: string; url: string; hidden: boolean; new: boolean }

/** A tracker on the Studio desk (GET /api/v1/newsroom/trackers): the public view plus its reports and how many are new. */
export interface DeskTracker {
  slug: string
  name: string
  kind: 'project' | 'rule' | 'rate'
  stages: string[]
  stage: number | null
  status: string
  status_date: string
  status_sources: string[]
  checked_at: string | null
  report_count: number
  new_count: number
  reports: DeskReport[]
  /** The model's reading of the new reports, already through the backend's checks; null when there is none or it failed them. */
  suggestion: Suggestion | null
  /** The status on the site is the model's checked line, put up by itself (NEWSROOM_TRACKER_AUTO). */
  auto_updated?: boolean
  /** Added from the topic finder (kept in the database, not a file). */
  from_studio?: boolean
}

/** `changed` false: the model found the reports only repeat the status. A checked change goes on the site by itself, unless
 *  `held` says why it waits for the owner (it moves to the last stage, or says the thing opened). */
export interface Suggestion { changed: boolean; status: string; stage: number | null; date: string; sources: string[]; reason: string; held?: string | null }

/** A "new tracker?" item from the weekly topic finder: several reports about one Pune subject no tracker follows, with a draft. */
export interface TrackerCandidate {
  key: string
  slug: string
  name: string
  kind: 'project' | 'rule' | 'rate'
  summary: string
  stages: string[]
  queries: string[]
  /** The model's first status line, through the checks; null when it failed them (the owner writes one). */
  status: string | null
  status_date: string
  report_count: number
  publishers: number
  by: 'model' | 'rules'
  reports: { date: string; title: string; source: string; url: string }[]
}

export interface NewTrackerBody { name: string; status: string; date: string; places: string[] }

export interface StatusBody { status: string; date: string; stage: number | null; sources: string[] }

export interface TrackersApi {
  list(): Promise<DeskTracker[]>
  setStatus(slug: string, body: StatusBody): Promise<DeskTracker>
  checked(slug: string): Promise<DeskTracker>
  hide(slug: string, reportId: string, hidden: boolean): Promise<DeskTracker>
  candidates(): Promise<TrackerCandidate[]>
  addCandidate(key: string, body: NewTrackerBody): Promise<DeskTracker>
  dismissCandidate(key: string): Promise<void>
}

export function createTrackersApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): TrackersApi {
  const base = opts.baseUrl ?? API_BASE_URL
  async function request<T>(path: string, json?: unknown): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    const token = opts.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
    if (json !== undefined) headers['Content-Type'] = 'application/json'
    let res: Response
    try {
      res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1/newsroom/trackers${path}`,
        { method: json === undefined ? 'GET' : 'POST', headers, body: json === undefined ? undefined : JSON.stringify(json) })
    } catch {
      throw new ApiError(0, 'Cannot reach the server. Check your internet.')
    }
    const text = await res.text()
    let data: unknown = null
    try { data = text ? JSON.parse(text) : null } catch { data = { detail: text.slice(0, 200) } }
    if (!res.ok) throw parseErrorBody(data, res.status)
    return data as T
  }
  const at = (slug: string) => `/${encodeURIComponent(slug)}`
  return {
    list: async () => { const r = await request<DeskTracker[]>(''); return Array.isArray(r) ? r : [] },
    setStatus: (slug, body) => request<DeskTracker>(`${at(slug)}/status`, body),
    checked: (slug) => request<DeskTracker>(`${at(slug)}/checked`, {}),
    hide: (slug, id, hidden) => request<DeskTracker>(`${at(slug)}/reports/${encodeURIComponent(id)}/hide`, { hidden }),
    candidates: async () => { const r = await request<TrackerCandidate[]>('/candidates'); return Array.isArray(r) ? r : [] },
    addCandidate: (key, body) => request<DeskTracker>(`/candidates/${encodeURIComponent(key)}/add`, body),
    dismissCandidate: async (key) => { await request(`/candidates/${encodeURIComponent(key)}/dismiss`, {}) },
  }
}

export const FIXTURE_TRACKERS: DeskTracker[] = [{
  slug: 'purandar-airport', name: 'Purandar airport', kind: 'project',
  stages: ['Site chosen', 'Land acquisition', 'Feasibility and design', 'Construction', 'Open'], stage: 2,
  status: 'Land acquisition is nearly done: the remaining 40 hectares is being taken compulsorily, and MADC has started appointing a consultant.',
  status_date: '2026-10-23', status_sources: ['Punekar News', 'Pune Mirror'], checked_at: null, report_count: 3, new_count: 1,
  suggestion: { changed: true, status: 'MADC is looking for global consultants for the feasibility study; the land acquisition is nearly done.',
    stage: 2, date: '2026-10-24', sources: ['Swarajya'], reason: 'The newest report says consultants are being sought.' },
  reports: [
    { id: 'r3', date: '2026-10-24', title: 'Maharashtra Revives Long-Delayed Purandar Airport Project, Seeks Global Consultants', source: 'Swarajya', url: 'https://example.com/3', hidden: false, new: true },
    { id: 'r2', date: '2026-10-23', title: 'Purandar Airport Project Moves Ahead as MADC Begins Consultant Appointment', source: 'Pune Mirror', url: 'https://example.com/2', hidden: false, new: false },
    { id: 'r1', date: '2026-10-21', title: 'Purandar Airport: Pune Administration to Compulsorily Acquire Remaining 40 Hectares', source: 'Punekar News', url: 'https://example.com/1', hidden: false, new: false },
  ],
}]

export const FIXTURE_CANDIDATES: TrackerCandidate[] = [{
  key: 'hadapsar-skywalk', slug: 'hadapsar-gadital-skywalk', name: 'Hadapsar Gadital skywalk', kind: 'project', summary: '',
  stages: ['Planned', 'Tendered', 'Built'], queries: ['Hadapsar skywalk'], status: 'The civic body has floated a tender for the skywalk.',
  status_date: '2026-11-26', report_count: 3, publishers: 3, by: 'model',
  reports: [
    { date: '2026-11-26', title: 'PMC plans skywalk at Hadapsar Gadital junction', source: 'Punekar News', url: 'https://example.com/s1' },
    { date: '2026-11-24', title: 'Hadapsar Gadital skywalk tender floated by civic body', source: 'Hindustan Times', url: 'https://example.com/s2' },
    { date: '2026-11-19', title: 'Hadapsar skywalk at Gadital to cost Rs 40 crore', source: 'Times of India', url: 'https://example.com/s3' },
  ],
}]

export function createFixtureTrackersApi(seed: DeskTracker[] = FIXTURE_TRACKERS, candidateSeed: TrackerCandidate[] = FIXTURE_CANDIDATES): TrackersApi {
  let rows = seed.map((t) => ({ ...t, reports: t.reports.map((r) => ({ ...r })) }))
  let cands = candidateSeed.map((c) => ({ ...c }))
  const find = (slug: string) => {
    const t = rows.find((x) => x.slug === slug)
    if (!t) throw new ApiError(404, 'No such tracker')
    return t
  }
  const fresh = (t: DeskTracker) => {
    const n = t.reports.filter((r) => r.new && !r.hidden).length
    return { ...t, new_count: n, suggestion: n ? t.suggestion : null }
  }
  return {
    list: async () => rows.map(fresh),
    setStatus: async (slug, body) => {
      const t = find(slug)
      if (body.status.trim().length < 12) throw new ApiError(422, 'Write the status in a sentence.')
      Object.assign(t, { status: body.status.trim(), status_date: body.date, stage: body.stage, status_sources: body.sources })
      t.reports.forEach((r) => { r.new = false })
      return fresh(t)
    },
    checked: async (slug) => { const t = find(slug); t.reports.forEach((r) => { r.new = false }); return fresh(t) },
    hide: async (slug, id, hidden) => {
      const t = find(slug)
      const r = t.reports.find((x) => x.id === id)
      if (!r) throw new ApiError(404, 'That report is not on this tracker')
      r.hidden = hidden
      rows = rows.map((x) => (x.slug === slug ? t : x))
      return fresh(t)
    },
    candidates: async () => cands.map((c) => ({ ...c })),
    addCandidate: async (key, body) => {
      const c = cands.find((x) => x.key === key)
      if (!c) throw new ApiError(422, 'That suggestion is gone: it was added or dismissed already.')
      if (body.status.trim().length < 12) throw new ApiError(422, 'Write the status in a sentence.')
      const t: DeskTracker = { slug: c.slug, name: body.name || c.name, kind: c.kind, stages: c.stages, stage: null, status: body.status.trim(),
        status_date: body.date, status_sources: [...new Set(c.reports.map((r) => r.source))].slice(0, 3), checked_at: null,
        report_count: c.reports.length, new_count: 0, suggestion: null, from_studio: true,
        reports: c.reports.map((r, i) => ({ id: `${c.key}-${i}`, date: r.date, title: r.title, source: r.source, url: r.url, hidden: false, new: false })) }
      rows = [...rows, t]
      cands = cands.filter((x) => x.key !== key)
      return t
    },
    dismissCandidate: async (key) => {
      if (!cands.some((x) => x.key === key)) throw new ApiError(404, 'That suggestion is gone')
      cands = cands.filter((x) => x.key !== key)
    },
  }
}

const real = createTrackersApi({ getToken })
let fake: TrackersApi | null = null
export const trackersApi = (): TrackersApi => (isFixtureMode() ? (fake ??= createFixtureTrackersApi()) : real)
