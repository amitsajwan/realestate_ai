/** Typed client for GET /api/v1/listings/{id}/sellers (who else markets this project). */
import { API_BASE_URL } from '@/lib/config/api'
import { getToken } from '@/lib/app/session'
import { ApiError, parseErrorBody } from '@/lib/app/api'

export interface SellerRow {
  /** Hostname without www., e.g. "99acres.com" or "31palmadrive-kharadi.in" */
  site: string
  title: string
  link: string
  /** Best organic Google position for this URL, or null for ads / platform entries */
  position: number | null
  /** true when this appeared as a Google Ad rather than an organic result */
  ad: boolean
}

export interface SellerGroups {
  /** Channel partners, microsites – other agents marketing the same project */
  agents: SellerRow[]
  /** Builder / promoter's own website */
  builder: SellerRow[]
  /** National and regional listing portals */
  portals: SellerRow[]
  /** Agents on avasetu.in with a live listing for the same project */
  platform: SellerRow[]
}

export interface SellersResult {
  /** ISO datetime of the web search that produced these results, or null if not searched yet */
  searched_at: string | null
  /** The Google query that was used, e.g. "Prasun Elara Lohegaon Pune" */
  query: string | null
  groups: SellerGroups
}

export async function fetchSellers(listingId: string): Promise<SellersResult> {
  const token = getToken()
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/listings/${encodeURIComponent(listingId)}/sellers`, { headers })
  } catch {
    throw new ApiError(0, 'Cannot reach the server.')
  }
  if (!res.ok) {
    let body: unknown = null
    try { body = await res.json() } catch { /* ignore */ }
    throw parseErrorBody(body, res.status)
  }
  return res.json() as Promise<SellersResult>
}
