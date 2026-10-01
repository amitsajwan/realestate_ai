/** Brand profile client for the agent's own Studio (GET/PATCH /join/site, upload through /uploads/images) with a fixture version. */
import { API_BASE_URL } from '@/lib/config/api'
import type { AgentBranding } from '@/lib/site/types'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { compressImage } from './imageCompress'
import { getToken } from './session'
import type { SiteUpdateInput } from './types'
import { api } from './client'

/** What the editor loads: the agent's identity plus his stored branding_data. */
export interface BrandingDoc {
  slug: string
  agent_name: string
  photo?: string
  branding_data: AgentBranding
}

export type BrandingPatch = Pick<SiteUpdateInput, 'business_name' | 'tagline' | 'about' | 'banner' | 'logo' | 'preset' | 'custom_primary' | 'rera_agent_no' | 'areas' | 'languages' | 'years_experience'>

export interface BrandingApi {
  load(): Promise<BrandingDoc>
  save(patch: BrandingPatch): Promise<BrandingDoc>
  upload(file: File): Promise<string>
}

/** Relative upload paths ('/uploads/images/x.jpg') are served by the API host. */
export function assetUrl(u?: string | null): string {
  if (!u) return ''
  return u.startsWith('/') ? API_BASE_URL.replace(/\/+$/, '') + u : u
}

async function call<T>(method: string, json?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let body: string | undefined
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  }
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/join/site`, { method, headers, body })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your internet.')
  }
  const text = await res.text()
  let data: unknown = null
  if (text) {
    try { data = JSON.parse(text) } catch { data = { detail: text.slice(0, 200) } }
  }
  if (!res.ok) throw parseErrorBody(data, res.status)
  return data as T
}

const realBranding: BrandingApi = {
  load: () => call<BrandingDoc>('GET'),
  save: (patch) => call<BrandingDoc>('PATCH', patch),
  upload: async (file) => {
    const [up] = await api.uploadImages([await compressImage(file)])
    if (!up?.url) throw new ApiError(422, 'Upload failed. Try a smaller JPG or PNG.')
    return up.url
  },
}

const FIXTURE_KEY = 'app_brand_fixture'
const fixtureBranding: BrandingApi = {
  async load() {
    let saved: BrandingDoc | null = null
    try { saved = JSON.parse(window.localStorage.getItem(FIXTURE_KEY) || 'null') } catch { /* ignore */ }
    return saved || { slug: 'demo', agent_name: 'Priya Deshmukh', branding_data: { business_name: 'Deshmukh Realty', preset: 'terracotta', areas: ['Baner', 'Aundh'], languages: ['English', 'Marathi'] } }
  },
  async save(patch) {
    const cur = await fixtureBranding.load()
    const b: Record<string, unknown> = { ...cur.branding_data }
    for (const [k, v] of Object.entries(patch)) {
      if (v === '' || v === null || (Array.isArray(v) && !v.length)) delete b[k]
      else b[k] = v
    }
    const next = { ...cur, branding_data: b as AgentBranding }
    try { window.localStorage.setItem(FIXTURE_KEY, JSON.stringify(next)) } catch { /* ignore */ }
    return next
  },
  async upload(file) {
    return api.uploadImages([file]).then((r) => r[0].url)
  },
}

/** What screens import: the fixture version in fixture mode, else the real one. */
export const brandingApi: BrandingApi = {
  load: () => (isFixtureMode() ? fixtureBranding : realBranding).load(),
  save: (p) => (isFixtureMode() ? fixtureBranding : realBranding).save(p),
  upload: (f) => (isFixtureMode() ? fixtureBranding : realBranding).upload(f),
}
