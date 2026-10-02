/**
 * Photo quality and visual review (backend/app/modules/photoquality).
 *
 * - The upload response carries `quality`, `enhanced_url` and `use_enhanced` per photo; listings keep them on each media record.
 * - Before upload, `analyzeFile` gives an instant, rough in-browser check (exposure, blur, size) with the same thresholds,
 *   so the photo step can show "Check: too dark" while the agent can still retake the shot.
 * - `POST /quality/review` returns the visual review of a calendar post, a news card or a listing's marketing cards.
 * Everything here is advice: nothing blocks posting or approval.
 */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export type PhotoIssue = 'dark' | 'bright' | 'blurry' | 'small' | 'tilted' | 'noisy' | 'mostly_sky_or_floor'

export interface PhotoQuality {
  score: number
  issues: string[]
  tips?: string[]
  enhanced_score?: number | null
  width?: number | null
  height?: number | null
}

/** The fields a photo record may carry (listing media, upload response). */
export interface QualityFields {
  url: string
  quality?: PhotoQuality | null
  enhanced_url?: string | null
  use_enhanced?: boolean | null
}

export const ISSUE_WORDS: Record<string, string> = {
  dark: 'too dark',
  bright: 'too bright',
  blurry: 'blurry',
  small: 'small',
  tilted: 'tilted',
  noisy: 'grainy',
  mostly_sky_or_floor: 'mostly floor or sky',
}

/** One short line per issue, for the agent on a phone. */
export const ISSUE_TIPS: Record<string, string> = {
  dark: 'Take it again with lights on',
  bright: 'Avoid pointing at the window or sun',
  blurry: 'Hold the phone still and tap to focus',
  small: 'Send the original photo, not a forwarded one',
  tilted: 'Hold the phone straight',
  noisy: 'More light helps more than zoom',
  mostly_sky_or_floor: 'Point the camera at the room',
}

export interface Badge {
  tone: 'good' | 'check'
  text: string
  tip: string | null
}

export function badgeFor(q: Pick<PhotoQuality, 'issues'> | null | undefined): Badge | null {
  if (!q) return null
  const issues = (q.issues ?? []).filter((i) => ISSUE_WORDS[i])
  if (!issues.length) return { tone: 'good', text: 'Good', tip: null }
  return { tone: 'check', text: `Check: ${issues.slice(0, 2).map((i) => ISSUE_WORDS[i]).join(', ')}`, tip: ISSUE_TIPS[issues[0]] ?? null }
}

/** The url to show: the enhanced copy when it exists and the toggle is on. */
export function displayUrl(m: QualityFields): string {
  return m.use_enhanced && m.enhanced_url ? m.enhanced_url : m.url
}

/** Keep only the quality fields of an upload response, ready to go on a media record. */
export function qualityFields(f: Partial<QualityFields> | null | undefined): Omit<QualityFields, 'url'> {
  if (!f || !f.quality) return {}
  const q = f.quality
  return {
    quality: { score: q.score, issues: q.issues ?? [], tips: (q.tips ?? []).slice(0, 4), enhanced_score: q.enhanced_score ?? null },
    ...(f.enhanced_url ? { enhanced_url: f.enhanced_url, use_enhanced: !!f.use_enhanced } : {}),
  }
}

// ---- instant in-browser check (same thresholds as the backend, measured at 640 px) ----
export const ANALYSIS_SIDE = 640
export const DARK_MEAN = 80
export const BRIGHT_MEAN = 195
export const BLUR_VAR = 50
export const SMALL_LONG = 800
export const SMALL_SHORT = 500

/** Rough quality from RGBA pixels already scaled to <= ANALYSIS_SIDE. `orig` is the photo's real size. */
export function analyzePixels(data: ArrayLike<number>, w: number, h: number, orig: { width: number; height: number } = { width: w, height: h }): PhotoQuality {
  const n = w * h
  const gray = new Float32Array(n)
  let sum = 0
  for (let i = 0, p = 0; i < n; i++, p += 4) {
    const g = 0.299 * data[p] + 0.587 * data[p + 1] + 0.114 * data[p + 2]
    gray[i] = g
    sum += g
  }
  const mean = n ? sum / n : 0
  // variance of the 4-neighbour Laplacian (what OpenCV computes with ksize=1)
  let ls = 0
  let ls2 = 0
  let cnt = 0
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x
      const l = gray[i - 1] + gray[i + 1] + gray[i - w] + gray[i + w] - 4 * gray[i]
      ls += l
      ls2 += l * l
      cnt++
    }
  }
  const lapVar = cnt ? ls2 / cnt - (ls / cnt) ** 2 : 0
  const issues: PhotoIssue[] = []
  if (mean < DARK_MEAN) issues.push('dark')
  else if (mean > BRIGHT_MEAN) issues.push('bright')
  if (cnt && lapVar < BLUR_VAR) issues.push('blurry')
  if (Math.max(orig.width, orig.height) < SMALL_LONG || Math.min(orig.width, orig.height) < SMALL_SHORT) issues.push('small')
  const penalty: Record<string, number> = { dark: 22, bright: 16, blurry: 26, small: 14 }
  const score = Math.max(0, Math.min(100, Math.round(100 - issues.reduce((s, i) => s + (penalty[i] ?? 10), 0))))
  return { score, issues, tips: issues.map((i) => ISSUE_TIPS[i]), width: orig.width, height: orig.height }
}

/** In-browser check of a picked photo. null when the browser cannot decode it (never blocks anything). */
export async function analyzeFile(file: File): Promise<PhotoQuality | null> {
  if (typeof document === 'undefined' || typeof createImageBitmap !== 'function' || !file.type.startsWith('image/')) return null
  try {
    const bmp = await createImageBitmap(file)
    const s = Math.min(1, ANALYSIS_SIDE / Math.max(bmp.width, bmp.height))
    const w = Math.max(1, Math.round(bmp.width * s))
    const h = Math.max(1, Math.round(bmp.height * s))
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(bmp, 0, 0, w, h)
    const q = analyzePixels(ctx.getImageData(0, 0, w, h).data, w, h, { width: bmp.width, height: bmp.height })
    bmp.close()
    return q
  } catch {
    return null
  }
}

// ---- visual review ----
export type ReviewKind = 'calendar' | 'news' | 'listing'

export interface QualityReview {
  score: number | null
  verdict: 'good' | 'fix' | 'redo' | null
  notes: string[]
  source: 'ai' | 'rules' | 'none'
  ai_available: boolean
  summary?: string
}

export const AI_UNAVAILABLE = 'AI review unavailable'

/** 'Quality 82/100 · Good' or 'Quality 54 · Check: text cut at the bottom'. */
export function reviewSummary(r: QualityReview | null | undefined): string {
  if (!r || r.score === null || r.score === undefined) return 'Quality: no image yet'
  if (r.verdict === 'good') return `Quality ${r.score}/100 · Good`
  const first = (r.notes ?? []).find((n) => n !== AI_UNAVAILABLE)
  return `Quality ${r.score} · Check${first ? `: ${first}` : ''}`
}

export function normalizeReview(raw: unknown): QualityReview {
  const r = (raw ?? {}) as Record<string, unknown>
  const verdict = r.verdict === 'good' || r.verdict === 'fix' || r.verdict === 'redo' ? r.verdict : null
  const source = r.source === 'ai' || r.source === 'rules' ? r.source : 'none'
  return {
    score: typeof r.score === 'number' ? Math.round(r.score) : null,
    verdict,
    notes: Array.isArray(r.notes) ? r.notes.map(String).slice(0, 6) : [],
    source,
    ai_available: r.ai_available === true,
  }
}

export interface QualityApi {
  review(kind: ReviewKind, id: string, refresh?: boolean): Promise<QualityReview>
}

export function createQualityApi(opts: { getToken: () => string | null; baseUrl?: string; fetchImpl?: typeof fetch }): QualityApi {
  const base = opts.baseUrl ?? API_BASE_URL
  return {
    async review(kind, id, refresh = false) {
      const headers: Record<string, string> = { Accept: 'application/json', 'Content-Type': 'application/json' }
      const token = opts.getToken()
      if (token) headers.Authorization = `Bearer ${token}`
      let res: Response
      try {
        res = await (opts.fetchImpl ?? fetch)(`${base}/api/v1/quality/review`, { method: 'POST', headers, body: JSON.stringify({ kind, id, refresh }) })
      } catch {
        throw new ApiError(0, 'Cannot reach the server. Check your internet.')
      }
      const text = await res.text()
      let data: unknown = null
      try {
        data = text ? JSON.parse(text) : null
      } catch {
        data = { detail: text.slice(0, 200) }
      }
      if (!res.ok) throw parseErrorBody(data, res.status)
      return normalizeReview(data)
    },
  }
}

const fixtureQuality: QualityApi = {
  async review(kind, id) {
    // deterministic per id, so screenshots and tests are stable
    const n = Array.from(`${kind}:${id}`).reduce((s, c) => s + c.charCodeAt(0), 0)
    return n % 3 === 0
      ? { score: 58, verdict: 'fix', notes: ['Text is close to the bottom edge', 'Busy background behind the headline'], source: 'ai', ai_available: true }
      : { score: 84, verdict: 'good', notes: [], source: 'ai', ai_available: true }
  },
}

const realQuality = createQualityApi({ getToken })

export const qualityApi: QualityApi = {
  review: (kind, id, refresh) => (isFixtureMode() ? fixtureQuality : realQuality).review(kind, id, refresh),
}
