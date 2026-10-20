/** Owner view of project-page enrichment: GET /api/v1/newsroom/project-enrichment (areastats.enrich.status_list). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { getToken } from './session'

export type EnrichStatus = 'ok' | 'partial' | 'failed' | 'parked' | 'waiting' | 'finished'

export interface EnrichItem {
  regno: string
  name: string
  status: EnrichStatus
  area: string | null
  enriched_at: string | null
  score: string | null
  failed: string[]
  checks: Record<string, string | string[] | null>
  page: string | null
  /** the last round crashed or ran too long (areastats.enrich.failed_round); parked after 3 in a row, for a fix offline */
  error?: string | null
  fails?: number
  parked_until?: string | null
  /** reading steps last run by an older version (enrich.VERSIONS): read again soon */
  outdated?: string[]
}

export interface EnrichList {
  counts: Record<EnrichStatus, number>
  items: EnrichItem[]
}

export async function getEnrichment(status?: EnrichStatus): Promise<EnrichList> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/newsroom/project-enrichment${status ? `?status=${status}` : ''}`, { headers })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your internet.')
  }
  const data = await res.json().catch(() => null)
  if (!res.ok) throw parseErrorBody(data, res.status)
  return data as EnrichList
}
