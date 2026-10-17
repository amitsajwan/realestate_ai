/** Studio client for /inbox/origins: per source (Google, Instagram, a tagged post link, direct...), the visitors, website chats and leads. */
import { isFixtureMode } from './client'
import { request } from './whatsapp'

export interface OriginRow {
  /** google | instagram | facebook | direct | unknown | a src= tag | another site's host */
  source: string
  visitors: number
  chats: number
  leads: number
  /** The published posts that carry this tag in their link, newest first (empty for Google, Direct, ...) */
  posts?: OriginPost[]
}

export interface OriginPost {
  url: string
  kind: string // post | reel
  channel?: string | null
  published_at?: string | null
  /** taken down from the Page since */
  removed?: boolean
}

export async function getOrigins(days = 7): Promise<{ days: number; rows: OriginRow[] }> {
  if (isFixtureMode()) return { days, rows: [] }
  return (await request<{ days: number; rows: OriginRow[] }>(`/inbox/origins?days=${days}`)) ?? { days, rows: [] }
}
