/** Small typed client for the agent-app API (docs/contracts/listing.md). No legacy AuthManager. */
import { API_BASE_URL } from '@/lib/config/api'
import { outcomePatchError } from './outcomes'
import type {
  AIDraft,
  AIDraftRequest,
  AppApi,
  BusinessToday,
  FollowupDraft,
  LeadPatch,
  ListingActivity,
  MarketingPack,
  MatchingLeads,
  PerformanceItem,
  Publication,
  SocialStatus,
  Lead,
  LeadDetail,
  Listing,
  ListingInput,
  ListingStatus,
  LoginResult,
  OtpRequested,
  SiteCreateInput,
  SiteResult,
  SiteUpdateInput,
  FacebookInterest,
  Stage,
  UploadedFile,
} from './types'

export class ApiError extends Error {
  status: number
  detail: string
  /** field name -> message, parsed from 422 bodies (FastAPI validation or publish "missing" lists). */
  fields: Record<string, string>
  /** Missing fields reported by publish 422 (or `network` errors have status 0). */
  missing: string[]

  constructor(status: number, detail: string, fields: Record<string, string> = {}, missing: string[] = []) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.fields = fields
    this.missing = missing
  }

  get isNetwork() {
    return this.status === 0
  }
}

/** Turn any error body into {detail, fields, missing}. Tolerant: the 422 shape for publish is not frozen. */
export function parseErrorBody(body: unknown, status: number): ApiError {
  const fields: Record<string, string> = {}
  let missing: string[] = []
  let detail = `Request failed (${status})`
  const b = body as Record<string, unknown> | null
  if (b && typeof b === 'object') {
    const d = (b.detail ?? b) as unknown
    if (typeof d === 'string') {
      detail = d
    } else if (Array.isArray(d)) {
      // FastAPI validation: [{loc:['body','price_inr'], msg:'...'}]  or a plain list of missing field names
      const msgs: string[] = []
      for (const item of d) {
        if (typeof item === 'string') {
          missing.push(item)
        } else if (item && typeof item === 'object') {
          const it = item as { loc?: unknown[]; msg?: string }
          const field = Array.isArray(it.loc) ? String(it.loc[it.loc.length - 1]) : ''
          const msg = it.msg ?? 'Invalid value'
          if (field && field !== 'body') fields[field] = msg
          msgs.push(msg)
        }
      }
      if (missing.length) detail = `Missing: ${missing.join(', ')}`
      else if (msgs.length) detail = msgs[0]
    } else if (d && typeof d === 'object') {
      const o = d as { missing?: unknown; message?: string; detail?: string }
      if (Array.isArray(o.missing)) missing = o.missing.map(String)
      detail = o.message ?? o.detail ?? (missing.length ? `Missing: ${missing.join(', ')}` : detail)
    }
    if (Array.isArray(b.missing)) missing = (b.missing as unknown[]).map(String)
  }
  for (const m of missing) fields[m] = fields[m] ?? 'Required'
  return new ApiError(status, detail, fields, missing)
}

export interface ClientOptions {
  baseUrl?: string
  getToken: () => string | null
  /** Called on a 401 for an authenticated request (clear the session and go to /join). */
  onUnauthorized?: () => void
  fetchImpl?: typeof fetch
}

export function createApiClient(opts: ClientOptions): AppApi {
  const base = opts.baseUrl ?? API_BASE_URL
  const doFetch = (...a: Parameters<typeof fetch>) => (opts.fetchImpl ?? fetch)(...a)

  async function request<T>(path: string, init: { method?: string; json?: unknown; form?: FormData } = {}): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    const token = opts.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
    let body: BodyInit | undefined
    if (init.form) {
      body = init.form // browser sets the multipart boundary
    } else if (init.json !== undefined) {
      headers['Content-Type'] = 'application/json'
      body = JSON.stringify(init.json)
    }
    let res: Response
    try {
      res = await doFetch(`${base}/api/v1${path}`, { method: init.method ?? 'GET', headers, body })
    } catch {
      throw new ApiError(0, 'Cannot reach the server. Check your internet.')
    }
    let data: unknown = null
    const text = await res.text()
    if (text) {
      try {
        data = JSON.parse(text)
      } catch {
        data = { detail: text.slice(0, 200) }
      }
    }
    if (!res.ok) {
      if (res.status === 401 && token) opts.onUnauthorized?.()
      throw parseErrorBody(data, res.status)
    }
    return data as T
  }

  const qs = (params: Record<string, string | number | undefined>) => {
    const p = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== '') p.set(k, String(v))
    const s = p.toString()
    return s ? `?${s}` : ''
  }

  return {
    requestOtp: (phone) => request<OtpRequested>('/join/otp/request', { method: 'POST', json: { phone } }),
    verifyOtp: (phone, code) => request<LoginResult>('/join/otp/verify', { method: 'POST', json: { phone, code } }),
    createSite: (input: SiteCreateInput) => request<SiteResult>('/join/site', { method: 'POST', json: input }),
    updateSite: (input: SiteUpdateInput) => request<unknown>('/join/site', { method: 'PATCH', json: input }),

    listListings: async (status?: ListingStatus) =>
      (await request<{ items: Listing[] }>(`/listings${qs({ status, limit: 100 })}`)).items,
    getListing: (id) => request<Listing>(`/listings/${id}`),
    createListing: (input: ListingInput) => request<Listing>('/listings', { method: 'POST', json: input }),
    updateListing: (id, patch) => request<Listing>(`/listings/${id}`, { method: 'PATCH', json: patch }),
    publishListing: (id) => request<Listing>(`/listings/${id}/publish`, { method: 'POST' }),
    setListingStatus: (id, status) => request<Listing>(`/listings/${id}/status`, { method: 'POST', json: { status } }),

    aiDraft: (req: AIDraftRequest) => {
      const form = new FormData()
      if (req.text && req.text.trim()) form.append('text', req.text.trim())
      if (req.audio) form.append('audio', req.audio, 'voice.webm')
      form.append('image_count', String(req.image_count))
      return request<AIDraft>('/listings/ai/draft', { method: 'POST', form })
    },

    // Legacy endpoint: POST /api/v1/uploads/images, multipart field `files`, response {success, files:[{url,...}]}.
    uploadImages: async (files: File[]) => {
      const form = new FormData()
      files.forEach((f) => form.append('files', f, f.name))
      const res = await request<{ files: UploadedFile[] }>('/uploads/images', { method: 'POST', form })
      if (!res.files || res.files.length < files.length) {
        // The endpoint silently skips files it fails to process; do not let a listing go out missing photos.
        throw new ApiError(422, `Only ${res.files?.length ?? 0} of ${files.length} photos uploaded. Try smaller JPG/PNG photos.`)
      }
      return res.files
    },

    listLeads: async (stage?: Stage) => (await request<{ leads: Lead[] }>(`/inbox/leads${qs({ stage, limit: 200 })}`)).leads,
    getLead: (id) => request<LeadDetail>(`/inbox/leads/${id}`),
    updateLead: (id, stageOrPatch, note) => {
      const patch: LeadPatch = typeof stageOrPatch === 'string' ? (note ? { stage: stageOrPatch, note } : { stage: stageOrPatch }) : stageOrPatch
      // Same rules as the API's 422s (docs/contracts/outcomes.md): fail fast instead of sending a request that is refused.
      const bad = outcomePatchError(patch)
      if (bad) return Promise.reject(new ApiError(422, bad, { outcome: bad }))
      return request<LeadDetail>(`/inbox/leads/${id}`, { method: 'PATCH', json: patch })
    },
    getToday: () => request<BusinessToday>('/inbox/today'),
    getFacebookInterest: () => request<FacebookInterest[]>('/engage/comments'),
    createFollowupDraft: (id, language) =>
      request<FollowupDraft>(`/inbox/leads/${id}/followup-draft`, { method: 'POST', json: language ? { language } : {} }),

    createMarketingPack: (listingId, language) =>
      request<MarketingPack>(`/listings/${listingId}/marketing`, { method: 'POST', json: language ? { language } : {} }),
    getMarketingPack: (listingId) => request<MarketingPack>(`/listings/${listingId}/marketing`),
    getMatchingLeads: (listingId) => request<MatchingLeads>(`/inbox/matching-leads${qs({ listing_id: listingId })}`),
    getPerformance: async () => (await request<{ items: PerformanceItem[] }>('/inbox/performance')).items ?? [],

    getListingActivity: (id, limit) => request<ListingActivity>(`/inbox/listings/${id}/activity${qs({ limit })}`),
    confirmAvailable: (id) => request<Listing>(`/listings/${id}/confirm-available`, { method: 'POST' }),

    getSocialStatus: () => request<SocialStatus>('/social/status'),
    publishToSocial: async (listingId, req) =>
      (
        await request<{ publications: Publication[] }>(`/social/listings/${listingId}/publish`, {
          method: 'POST',
          json: { channels: req.channels, approve: req.approve, consent: req.consent, force: req.force ?? false },
        })
      ).publications ?? [],
    listPublications: async (listingId) =>
      (await request<{ items: Publication[] }>(`/social/listings/${listingId}/publications`)).items ?? [],
    retryPublication: (id) => request<Publication>(`/social/publications/${id}/retry`, { method: 'POST' }),
  }
}
