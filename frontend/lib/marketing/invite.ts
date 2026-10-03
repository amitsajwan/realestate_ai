import { API_BASE_URL } from '@/lib/config/api'
import { normalizeIndianMobile } from '@/lib/site/phone'
import { INVITE } from './strings'

export const INVITE_URL = API_BASE_URL + '/api/v1/join/request-invite'

export interface InviteFields {
  name: string
  phone: string
  city: string
  message: string
  consent: boolean
}
export type InviteErrors = Partial<Record<'name' | 'phone' | 'city' | 'message' | 'consent', string>>

export function validateInvite(f: InviteFields): { errors: InviteErrors; phone: string | null } {
  const errors: InviteErrors = {}
  const phone = normalizeIndianMobile(f.phone)
  if (f.name.trim().length < 2 || f.name.trim().length > 100) errors.name = INVITE.errors.name
  if (!phone) errors.phone = INVITE.errors.phone
  if (f.city.trim().length < 2 || f.city.trim().length > 60) errors.city = INVITE.errors.city
  if (f.message.trim().length > 500) errors.message = INVITE.errors.message
  if (!f.consent) errors.consent = INVITE.errors.consent
  return { errors, phone }
}

export type SubmitResult = 'ok' | 'rate_limited' | 'invalid' | 'error'

/** The ?src= tag of the link the visitor came in on (wa, fbgroup, ig...), so the owner sees which channel brings agents. */
export function sourceTag(search: string = typeof window !== 'undefined' ? window.location.search : ''): string | undefined {
  const v = (new URLSearchParams(search).get('src') || '').toLowerCase().replace(/[^a-z0-9_-]/g, '').slice(0, 40)
  return v || undefined
}

/** POST the request. `website` is the honeypot: sent as-is (empty for real people). */
export async function submitInviteRequest(f: InviteFields & { phone: string; website: string }): Promise<SubmitResult> {
  try {
    const res = await fetch(INVITE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: f.name.trim(),
        phone: '+91' + f.phone,
        city: f.city.trim(),
        message: f.message.trim() || undefined,
        consent: f.consent,
        website: f.website,
        source: sourceTag(),
      }),
    })
    if (res.ok) return 'ok'
    if (res.status === 429) return 'rate_limited'
    if (res.status === 422) return 'invalid'
    return 'error'
  } catch {
    return 'error'
  }
}
