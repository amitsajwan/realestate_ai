/** Studio client for /interest/report: every tracked link (one per post, home and channel) with visits, taps and leads. */
import { isFixtureMode } from './client'
import { request } from './whatsapp'

export interface InterestLinkStats {
  code: string
  kind: 'listing' | 'post' | 'page'
  ref: string
  channel: string
  url: string
  title: string
  created_at: string
  clicks: number
  interests: number
  leads: number
  leads_with_phone: number
}

export async function getInterestReport(): Promise<InterestLinkStats[]> {
  if (isFixtureMode()) return []
  const data = await request<{ links: InterestLinkStats[] }>('/interest/report')
  return data?.links ?? []
}
