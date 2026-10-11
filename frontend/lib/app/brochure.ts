/** Brochure kit: typed client for /listings/{id}/brochure (upload a PDF, confirm what it says, answer the registration question),
 *  a fixture fake for local work, and small helpers the card and its tests share. */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export type FactState = 'pending' | 'confirmed' | 'dropped'
export type RegistrationStatus = 'verified' | 'unverified' | 'unknown' | 'registered_by_agent' | 'exempt'
export type FactValue = string | number | boolean | string[] | null | Record<string, unknown>

export interface BrochureFact {
  id: string
  key: string
  label: string
  value: FactValue
  /** 1-based page the fact was read from. */
  page: number
  /** The exact words on the page. */
  quote: string
  level: 'builder_claim'
  state: FactState
  edited: boolean
}

export type BrochureImageKind = 'floor_plan' | 'master_plan' | 'location_map' | 'render'

/** A page kept as a large image because its text says it is a plan, a map or a render. Posts use it only once it is `confirmed`. */
export interface BrochureImage {
  id: string
  /** 1-based page the image is. */
  page: number
  kind: BrochureImageKind
  /** "Artist's impression" on every render; null otherwise. */
  label: string | null
  /** Server path of the JPEG (needs the agent's token; use `BrochureApi.image`). */
  url: string
  state: FactState
}

export interface BrochureRegistration {
  status: RegistrationStatus
  rera_no: string | null
  note: string
}

export interface BrochureKit {
  id: string
  listing_id: string
  filename: string
  pages: number
  image_only_pages: number[]
  status: 'done' | 'failed'
  error?: string
  read_at: string | null
  facts: BrochureFact[]
  registration: BrochureRegistration
  /** Plans, maps and renders kept from the brochure (absent on kits read before images were kept). */
  images?: BrochureImage[]
}

export type RegistrationAnswer = { status: 'registered'; rera_no: string } | { status: 'exempt' }

export interface BrochureApi {
  /** The kit, or null when no brochure was uploaded (404). */
  get(listingId: string): Promise<BrochureKit | null>
  /** Upload a PDF; `onProgress` gets 0..1 while the bytes go up. The server reads it before answering. */
  upload(listingId: string, file: File, onProgress?: (fraction: number) => void): Promise<BrochureKit>
  setFact(listingId: string, factId: string, state: FactState, value?: FactValue): Promise<BrochureKit>
  setRegistration(listingId: string, answer: RegistrationAnswer): Promise<BrochureKit>
  /** A browser URL for page `n`'s thumbnail (the image needs the bearer token, so it is fetched and kept as an object URL). */
  pageImage(listingId: string, n: number): Promise<string>
  /** Use (confirmed), don't use (dropped) or undecided (pending) for one image. */
  setImage(listingId: string, imageId: string, state: FactState): Promise<BrochureKit>
  /** An object URL of the image, fetched with the token once. */
  image(listingId: string, imageId: string): Promise<string>
}

export const BROCHURE_MAX_MB = 30
export const BROCHURE_MAX_BYTES = BROCHURE_MAX_MB * 1024 * 1024
export const BROCHURE_MAX_PAGES = 40

/** Why this file cannot be uploaded, or null when it can. Checked before sending 30 MB over a phone connection. */
export function brochureFileError(file: Pick<File, 'name' | 'type' | 'size'>): string | null {
  const isPdf = file.type === 'application/pdf' || (!file.type && /\.pdf$/i.test(file.name))
  if (!isPdf) return 'Choose a PDF file. The brochure must be a PDF.'
  if (file.size === 0) return 'This file is empty. Choose the brochure PDF again.'
  if (file.size > BROCHURE_MAX_BYTES) {
    return `This PDF is ${(file.size / (1024 * 1024)).toFixed(1)} MB. The limit is ${BROCHURE_MAX_MB} MB.`
  }
  return null
}

/** MahaRERA project numbers: P5 followed by digits (e.g. P52100076768). Spaces are ignored and letters upper-cased. */
export function normaliseReraNo(raw: string): string {
  return raw.replace(/\s+/g, '').toUpperCase()
}
export function isReraNo(raw: string): boolean {
  return /^P5\d{6,}$/.test(normaliseReraNo(raw))
}

export const pendingFacts = (kit: BrochureKit | null) => (kit ? kit.facts.filter((f) => f.state === 'pending') : [])
export const kitImages = (kit: BrochureKit | null): BrochureImage[] => kit?.images ?? []
export const needsRegistrationAnswer = (kit: BrochureKit | null) =>
  !!kit && (kit.registration.status === 'unknown' || kit.registration.status === 'unverified')

export function friendlyBrochureError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 413) return `This PDF is too big. The limit is ${BROCHURE_MAX_MB} MB and ${BROCHURE_MAX_PAGES} pages.`
    if (e.status === 415) return 'Choose a PDF file. The brochure must be a PDF.'
    if (e.status === 404) return 'This listing or brochure was not found. Go back and refresh.'
    return e.detail
  }
  return e instanceof Error ? e.message : 'Something went wrong'
}

type XhrLike = Pick<XMLHttpRequest, 'open' | 'setRequestHeader' | 'send' | 'status' | 'responseText'> & {
  upload: { onprogress: ((ev: { lengthComputable: boolean; loaded: number; total: number }) => void) | null } | null
  onload: (() => void) | null
  onerror: (() => void) | null
  onabort?: (() => void) | null
}

function parseText(text: string): unknown {
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return { detail: text.slice(0, 200) }
  }
}

export function createBrochureApi(opts: {
  getToken: () => string | null
  baseUrl?: string
  fetchImpl?: typeof fetch
  /** Upload transport; XMLHttpRequest by default because fetch cannot report upload progress. */
  xhr?: () => XhrLike
}): BrochureApi {
  const base = opts.baseUrl ?? API_BASE_URL
  const enc = encodeURIComponent
  const root = (lid: string) => `/listings/${enc(lid)}/brochure`
  const auth = (): Record<string, string> => {
    const token = opts.getToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  async function send(path: string, init: { method?: string; json?: unknown } = {}): Promise<Response> {
    const headers: Record<string, string> = { Accept: 'application/json', ...auth() }
    let body: string | undefined
    if (init.json !== undefined) {
      headers['Content-Type'] = 'application/json'
      body = JSON.stringify(init.json)
    }
    try {
      return await (opts.fetchImpl ?? fetch)(`${base}/api/v1${path}`, { method: init.method ?? 'GET', headers, body })
    } catch {
      throw new ApiError(0, 'Cannot reach the server. Check your internet.')
    }
  }

  async function request<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
    const res = await send(path, init)
    const data = parseText(await res.text())
    if (!res.ok) throw parseErrorBody(data, res.status)
    return data as T
  }

  const thumbs = new Map<string, Promise<string>>()
  /** GET a JPEG with the token once; a failure is tried again next time. */
  const blobUrl = (key: string, path: string, what: string): Promise<string> => {
    let p = thumbs.get(key)
    if (!p) {
      p = (async () => {
        const res = await send(path)
        if (!res.ok) throw new ApiError(res.status, `${what} could not be shown`)
        return URL.createObjectURL(await res.blob())
      })()
      p.catch(() => thumbs.delete(key))
      thumbs.set(key, p)
    }
    return p
  }

  return {
    get: async (lid) => {
      try {
        return await request<BrochureKit>(root(lid))
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) return null
        throw e
      }
    },

    upload: (lid, file, onProgress) =>
      new Promise<BrochureKit>((resolve, reject) => {
        const x = opts.xhr ? opts.xhr() : (new XMLHttpRequest() as unknown as XhrLike)
        x.open('POST', `${base}/api/v1${root(lid)}`)
        x.setRequestHeader('Accept', 'application/json')
        for (const [k, v] of Object.entries(auth())) x.setRequestHeader(k, v)
        if (x.upload && onProgress) {
          x.upload.onprogress = (ev) => {
            if (ev.lengthComputable && ev.total > 0) onProgress(Math.min(1, ev.loaded / ev.total))
          }
        }
        x.onload = () => {
          const data = parseText(x.responseText)
          if (x.status >= 200 && x.status < 300) {
            onProgress?.(1)
            resolve(data as BrochureKit)
          } else reject(parseErrorBody(data, x.status))
        }
        x.onerror = () => reject(new ApiError(0, 'The upload stopped. Check your internet and try again.'))
        x.onabort = () => reject(new ApiError(0, 'The upload was cancelled.'))
        const form = new FormData()
        form.append('file', file, file.name)
        x.send(form)
      }),

    setFact: (lid, fid, state, value) =>
      request<BrochureKit>(`${root(lid)}/facts/${enc(fid)}`, {
        method: 'PATCH',
        json: value === undefined ? { state } : { state, value },
      }),

    setRegistration: (lid, answer) =>
      request<BrochureKit>(`${root(lid)}/registration`, {
        method: 'POST',
        json: answer.status === 'registered' ? { status: 'registered', rera_no: normaliseReraNo(answer.rera_no) } : { status: 'exempt' },
      }),

    pageImage: (lid, n) => blobUrl(`${lid}:${n}`, `${root(lid)}/pages/${n}.jpg`, `Page ${n}`),

    setImage: (lid, iid, state) => request<BrochureKit>(`${root(lid)}/images/${enc(iid)}`, { method: 'PATCH', json: { state } }),

    image: (lid, iid) => blobUrl(`${lid}:img:${iid}`, `${root(lid)}/images/${enc(iid)}.jpg`, 'The image'),
  }
}

/** A small kit like the reader returns for a typical project brochure. */
export function sampleKit(listingId: string, filename = 'brochure.pdf'): BrochureKit {
  return {
    id: `fx-kit-${listingId}`,
    listing_id: listingId,
    filename,
    pages: 12,
    image_only_pages: [5, 6, 9],
    status: 'done',
    read_at: new Date().toISOString(),
    facts: [
      { id: 'f1', key: 'project_name', label: 'Project', value: 'Gulmohar City Phase 2', page: 1, quote: 'Gulmohar City Phase 2', level: 'builder_claim', state: 'pending', edited: false },
      { id: 'f2', key: 'amenities', label: 'Amenities', value: ['Clubhouse', 'Swimming pool', 'Gym', "Children's play area"], page: 4, quote: 'Clubhouse | Swimming pool | Gym | Children’s play area', level: 'builder_claim', state: 'pending', edited: false },
      { id: 'f3', key: 'configurations', label: 'Configurations', value: ['1 BHK', '2 BHK'], page: 7, quote: 'Spacious 1 & 2 BHK homes', level: 'builder_claim', state: 'pending', edited: false },
      { id: 'f4', key: 'flooring', label: 'Flooring', value: 'Vitrified tiles in all rooms', page: 8, quote: '2x2 vitrified tiles in all rooms', level: 'builder_claim', state: 'pending', edited: false },
    ],
    registration: { status: 'unknown', rera_no: null, note: 'No MahaRERA number was found in the brochure.' },
    images: [
      { id: 'i1', page: 1, kind: 'render', label: "Artist's impression", url: `/api/v1/listings/${listingId}/brochure/images/i1.jpg`, state: 'pending' },
      { id: 'i7', page: 7, kind: 'floor_plan', label: null, url: `/api/v1/listings/${listingId}/brochure/images/i7.jpg`, state: 'pending' },
    ],
  }
}

const PLACEHOLDER_PAGE =
  'data:image/svg+xml;charset=utf-8,' +
  encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="420"><rect width="300" height="420" fill="#f3f4f6"/><text x="150" y="215" font-family="sans-serif" font-size="28" text-anchor="middle" fill="#6b7280">Brochure page</text></svg>')

/** Local/dev fake: any PDF becomes the sample kit; answers change it the way the server would. */
export function createFixtureBrochureApi(): BrochureApi {
  const kits = new Map<string, BrochureKit>()
  const need = (lid: string) => {
    const k = kits.get(lid)
    if (!k) throw new ApiError(404, 'Upload the brochure first')
    return k
  }
  const copy = (k: BrochureKit): BrochureKit => ({
    ...k,
    facts: k.facts.map((f) => ({ ...f })),
    registration: { ...k.registration },
    images: (k.images ?? []).map((i) => ({ ...i })),
  })
  return {
    get: async (lid) => {
      const k = kits.get(lid)
      return k ? copy(k) : null
    },
    upload: async (lid, file, onProgress) => {
      const err = brochureFileError(file)
      if (err) throw new ApiError(422, err)
      for (const f of [0.25, 0.5, 0.75, 1]) onProgress?.(f)
      const k = sampleKit(lid, file.name)
      kits.set(lid, k)
      return copy(k)
    },
    setFact: async (lid, fid, state, value) => {
      const k = need(lid)
      const f = k.facts.find((x) => x.id === fid)
      if (!f) throw new ApiError(404, 'This fact was not found')
      f.state = state
      if (value !== undefined) {
        f.value = value
        f.edited = true
      }
      return copy(k)
    },
    setRegistration: async (lid, answer) => {
      const k = need(lid)
      k.registration =
        answer.status === 'registered'
          ? { status: 'registered_by_agent', rera_no: normaliseReraNo(answer.rera_no), note: 'Entered by you. Not found on MahaRERA yet.' }
          : { status: 'exempt', rera_no: null, note: 'You said this project does not need MahaRERA registration.' }
      return copy(k)
    },
    pageImage: async () => PLACEHOLDER_PAGE,
    setImage: async (lid, iid, state) => {
      const k = need(lid)
      const im = (k.images ?? []).find((x) => x.id === iid)
      if (!im) throw new ApiError(404, 'This image was not found')
      im.state = state
      return copy(k)
    },
    image: async () => PLACEHOLDER_PAGE,
  }
}

const real = createBrochureApi({ getToken })
let fake: BrochureApi | null = null
const pick = () => (isFixtureMode() ? (fake ??= createFixtureBrochureApi()) : real)
/** The API screens use: the fixture fake in fixture mode, else the server. */
export const brochureApi: BrochureApi = {
  get: (...a) => pick().get(...a),
  upload: (...a) => pick().upload(...a),
  setFact: (...a) => pick().setFact(...a),
  setRegistration: (...a) => pick().setRegistration(...a),
  pageImage: (...a) => pick().pageImage(...a),
  setImage: (...a) => pick().setImage(...a),
  image: (...a) => pick().image(...a),
}
