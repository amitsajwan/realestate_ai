/** Studio client for /inbox/origins: per source (Google, Instagram, a tagged post link, direct...), the visitors, website chats and leads. */
import { isFixtureMode } from './client'
import { request } from './whatsapp'

export interface OriginRow {
  /** google | instagram | facebook | direct | unknown | a src= tag | another site's host */
  source: string
  visitors: number
  chats: number
  leads: number
}

export async function getOrigins(days = 7): Promise<{ days: number; rows: OriginRow[] }> {
  if (isFixtureMode()) return { days, rows: [] }
  return (await request<{ days: number; rows: OriginRow[] }>(`/inbox/origins?days=${days}`)) ?? { days, rows: [] }
}
